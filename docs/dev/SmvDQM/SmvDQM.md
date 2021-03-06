# SmvDQM Framework

Extracted from issues:
* #176
* #178
* #179

## Use Cases

## Use DQM in SmvApp/SmvModule Framework

### Create DQM
At `SmvDataSet` level, a `dqm` method need to be created with returning an empty SmvDQM. The dqm method could be override by concrete SmvModules or SmvFiles.

```scala
object CoolModule1 extends SmvModule("This is a cool module") {
   override def requiresDS() = Seq(***)
   override def run(***) = {***}
   override def dqm() = SmvDQM().
      add(rule1).
      add(fix1).
      add(policy1).
      ...
}
```

The `SmvDQM` builder interface will be defined in the next session.

Please note that since `dqm` method is on `SmvDataSet` level, for `SmvFile`s, it's better to
create new `SmvFile` objects by extending the base class instead of through a simple constructor
of `SmvFile`, so that the `dqm` method can be override. One step further, `SmvFile` object can
also have a nontrivial `run` method.

### Attach DQM
As long as the dqm is not empty, the `SmvDQM` object will be "attached" to the `DataFrame`
generated by the `run` method of the `SmvDataSet`. It happens when we call `doRun` method of
that `SmvDataSet` from the `SmvApp`:

```
SmvApp::resolveRDD -> SmvDataSet::rdd -> computeDataFrame -> doRun
```

The `doRun` method then will looks like
```scala
def doRun {
  val resultDf = run()
  df.attachDQM(dqm)
}
```

Please note that when a `SmvDQM` attached to a `DataFrame` the counters and logger in the
`SmvDQM` are not updated yet, since no action happens on the `DataFrame` yet.
We need to collect the results when the first action happens on the df.

### Check DQM results and apply policy
There are 2 types of approaches to collect the results and apply policies:

* Create an monitoring mechanism to keep tracking of the actions on the df created by a `SmvDataSet`
* For any `SmvDataSet` with none empty `dqm`, force an action. For example, do a count or persist

The "monitoring" approach is very hard to implement, since although we can keep an eye on all
the actions triggered by the `SmvApp` framework, there is no obvious way for us to keep tracking
of actions within client code.

For the "force-an-action" approach, we can either do the action just after attaching dqm in the
`doRun` method:
```scala
def doRun {
  val resultDf = run().attachDQM(dqm)
  resultDf.checkDQM(dqm, isForceAction) // call count at the beginning of checkDQM
  resultDf
}
```

Or we can call `checkDQM` after persisting or force an action for `isEphemeral` case.
```scala
def computeDataFrame() {
  if(isEphemeral) {
    val resultDf = doRun()        // attachDQM is in the doRun method
    resultDf.checkDQM(dqm, isForceAction = true)
    resultDf
  } else {
    readPersistedFile() recoverWith {case e =>
      persist(doRun)
      val rddReadBack = readPersistedFile(prefix).get
      rddReadBack.checkDQM(dqm, isForceAction = false)
      rddReadBack
    }
  }
}
```

We will take above approach and do it in the `compureRDD` method, so that we
don't need to apply an extra action when `persist` happens.

### Handle Data parsing rejections

In the current file reading reject logging implementation, there is an `SmvApp` level
`RejectLogger`. Depend on the error handling policy for each `SmvFile`, they could log
the rejected records to the app level logger.

It was designed that way since before the `DQM` idea, we don't have control on when a data
read action really happens.

With the DQM framework, since we will either force an action or do a persist
(also an action) before we hand over the DF to downstream `SmvModule`s, at the same time we
check the DQM, we should check the `RejectLogger`. Therefore we can keep the logger to `SmvFile`
level.

Since both parser and `DQM` can reject records, we will name the `RejectLogger` in `SmvFile` as
`parserLogger`.

Since only `SmvFile` can potentially reject records from the parser, we need to add the
 `checkParserLogger` into `SmvFile`'s `computeDataFrame` method.

In case of parsing error happens, we either
* Print the log and keep going, or
* Print the log and Terminate

A `SmvFile` level flag `failAtParsingError` will be defined with default value `true`. User
defined `SmvFile` can override it.
`checkParserLogger` with take that flag and determine whether the check is passed or not.

Both `checkDQM` and `checkParserLogger` will return a `CheckResult` object which contains:
* `passed: Boolean` - whether the DQM is passed
* `errorMessages: Seq[(String, String)]` - list of policy name - error message pair on failed policies
* `checkLog`: Seq[String] - all (including non-critical) reports on all the DQM and parser
loggers

`CheckResult` will have a `++` operator which combines multiple check results.

Neither `checkDQM` nor `checkParserLogger` will terminate the process. Another method,
`terminateAtError`, will take `CheckRule` object as input and determine whether terminate or
not.

With all those together, the `computeDataFrame` method on `SmvFile` will looks like,
```scala
def computeDataFrame() {
  val (df, hasActionYet) = if(isEphemeral) {
    (doRun(), false)
  } else {
    val resultDf = readPersistedFile() recoverWith {case e =>
      persist(doRun)
      readPersistedFile(prefix).get
    }
    (resultDf, true)
  }

  val checkResult = {
    if(!hasActionYet) df.count
    checkParserLogger ++ df.checkDQM
  }

  terminateAtErrot(checkResult)
  df
}
```

### Persist DQM results

By default a `SmvFile` "isEphemeral". In that case, it
will be forced to do an action whenever it is accessed. However since the data file itself does
not change, the DQM results and the parsing logger should be the same. We can actually
persist the results in a "filename.hashOfHash.check" file, and as long as that file is there,
we don't need to run `checkDQM` or `checkParserLogger` anymore.

Let's modify the `checkResult` part of the `computeDataFrame` method
```scala
val checkResult = readPersistedCheckFile() recoverWith {case e =>
  if(!hasAction) df.count
  val res = checkParserLogger ++ df.checkDQM
  res.persist
  res
}
```

Please not that the `hashOfHash` is part of the file name, so that if either of the original
file changed or the code of the SmvFile changed (including dqm definition part) the
`readPersistedCheckFile` will fail and new check will be performed.

### Combine Parser check and DQM to a single ValidationSet

Since parser check and DQM check shares the same need of handling the timing of the action on the result
DF of a `SmvDataSet`, we can create an abstract class `ValidationTask` and make `SmvDQM` and
`ParserValidation` as 2 concrete class of `ValidationTask`. Also we will create `ValidationSet` class, which
will contain one or more `ValidationTask`s.

We will move the following functions to methods of `ValidationSet`:
* Force action on a DF
* `CheckResult` operation
* Terminate at error
* `CheckResult` persisting and read back

With this framework, the `computeDataFrame` method can be uniquely defined in `SmvDataSet` level without
splitting to different versions in `SmvFile` and `SmvModule`
```scala
def computeDataFrame() {
  val (df, hasActionYet) = if(isEphemeral) {
    (doRun(), false)
  } else {
    val resultDf = readPersistedFile() recoverWith {case e =>
      persist(doRun)
      readPersistedFile(prefix).get
    }
    (resultDf, true)
  }

  dataValidationSet.validate(df, hasActionYet)
  df
}
```

The difference between `SmvFile` and `SmvModule` will be the set of `ValidationTask`s in the `ValidationSet`.
In general, an `SmvFile` will have a `ParserValidation` task, and an `SmvDQM` task, while `SmvModule` only
will only have an `SmvDQM` task.

The `validate` method of `ValidationSet` will looks like:
```scala
def validate(df: DataFrame, hasActionYet: Boolean) = {
  val needAction = tasks.map{t => t.needAction}.reduce(_ || _)
  val result = readPersistedCheckFile() recover with {case e =>
    if((!hasActionYet) && needAction) forceAction(df)
    val res = tasks.map{t => t.validate(df)}.reduce(_ ++ _)
    persiste(res)
    res
  }
  terminateAtError(result)
}
```

## DQM interface
DQM is a sub-package, `org.tresamigos.smv.dqm`, of SMV.

### Creating Rules

```scala
val rules = SmvDQM().
    add(Rule($"age" < 150, "ageLT150"), FailAny).
    add(BoundRule($"age", 1, 150), FailCount(10)).
    add(Fix( $"age" > 150, lit(150) as 'age, name = "ageFix150")).
    add(BoundFix($"age", 1, 150, name = "ageFix1-150")).
    add(FailTotalRuleCountPolicy(30))
    ...
```

The `SmvDQM` is a builder which takes `add` method with 2 signatures
* `add(rule: DQMRule, taskPolicy: DQMTaskPolicy = FailNone)`
* `add(fix: DQMFix, taskPolicy: DQMTaskPolicy = FailNone)`
* `add(policy: DQMPolicy)`

`DQMTask` is an abstract class with 2 concrete classes: `DQMRule` and `DQMFix`.
* A `DQMRule` is applied on records. If any record violates the Rule, the entire record will be rejected.
* A `DQMFix` is applied to a cell of a record and fix the cell while keep the record.

A `DQMPolicy` is applied on the entire DF with checking both the DF and the log of the
`DQMTask` results.

Each `DQMTask` associates with a `DQMTaskPolicy`.

A `DQMTaskPolicy` can be mapped to a `DQMPolicy` which only depends on the specific Task's result.
`DQMTaskPolicy` has 4 case class/objects:
* `FailNone` - policy check never fails even if some records are rejected. Map to an empty policy
* `FailAny` - policy check fails if any record get rejected by the CheckRule (same as FailCount(1)), map to `ImplementFailCountPolicy`
* `FailCount(n)` - policy check fails if more than or equal n records get rejected by the CheckRule, map to `ImplementFailCountPolicy`
* `FailPercent(r)` - policy check fails is more than or equal r percent records get rejected by the CheckRule. The percentage `r` is a float between 0 and 1, map to `ImplementFailPercentPolicy`

There are 4 public case class extends `DQMPolicy`:
* `FailTotalRuleCountPolicy(n)`
* `FailTotalRulePercentPolicy(r)`
* `FailTotalFixCountPolicy(n)`
* `FailTotalFixPercentPolicy(r)`

Which will combine all the rule or fix counts and check the policies. For example, if in total there are 2 rules defined, one for checking the `age` field and the other checking `amt` field, we can defined a `FailTotalRuleCountPolicy(1000)`. The `DF` will fail the policy if add up together there are more than or equal 1000 records get rejected by the 2 rules.

We can extend DQMRule and DQMFix for specific common cases to make the code clearer.  See example below. Note: only the rules are shown below, there would be an equivalent "Fix" method that takes a default value.
```scala
val rules = SmvDQM().
    add(FormatRule($"age", """^[A-Z]""".r)).
    add(SetRule($"gender", Seq("M", "F"))).
    ...
```

### User defined Rules, Fixes and Policies

A Rule can be defined with a `Column` which returns a BooleanType. So user can extends `DQMRule` to define new rules. For example,
```scala
case class DoubleOpenBoundRule(c: Column, upper: Double, lower: Double)
  extends DQMRule(c < lit(upper) && c > lit(lower), name = s"OpenBound(${c})")
```

User defined `DQMFix` interface
```scala
case class SetFix(c: Column, validVals: Seq[String], default: String)
  extends DQMFix(! c.in(validVals.map{s => lit(s)}: _*), lit(default), name = "SetFix(${c})")
```

User defined `DQMPolicy` interface
```scala
DQMPolicy(policy: (DataFrame, DQMState) => Boolean, name: String)
```

### Applying the DQM
Once the DQM (set of rules, fixes, policies) have been created, they can be applied to a `DataFrame`.  As a matter of fact, the same set of rules can be applied to multiple `DataFrame`s.
```scala
dqm.applyOnDF(df)
```

Internally, since we want to avoid introducing an extra *Action* to the `DataFrame` just for DQM, we split the `applyToDF` method to 2 steps:
* attachTasks, and
* checkPolicies

where the first step will simply apply the Rules and Fixes to the DF as projections and filters (*Transformations*, instead of *Actions*).
After that we could trigger an *Action* Within SmvApp framework. After the action, `checkPolicies` will be called, which will collect the results from the Rules and Fixes and
also potentially apply checks agains any operation on the output DF.

When `DQM` is used outside of the App framework, the `applyOnDF` method should be used, which actually force an action on the DF.

#### DQMState
In between of the `attachTasks` and `checkPolicies` methods, a `DQMState` will be used to pass the
information.

There are a group of accumulators in the `DQMState`:
* One `Accumulator[Long]` for overall number of records
* Each `DQMRule` has one `RejectLogger`, which has the number of rejected records and some examples for debug
* Each `DQMFix` has one `Accumulator[Long]` for number of fixes

A group of methods in `DQMState` should be used to add records and report.

When the action on a DF happens, a specific method, `snapshot`, need to be called on `DQMState` to get the
static copy of the result. The reason is that the `Accumulator`s could keep accumulating when there are
multiple actions in the policies.

#### `attachTasks` (private[smv])
```scala
val resDf = dqm.attachTasks(df)
```

This method will convert the `DQMRule`s an `DQMFix`s to a group of transformations on the DF. Also an `pipeCount` will be attached.

#### `checkPolicies` (private[smv])
```scala
val dqmRes = dqm.checkPolicies(df)
```
Depending on the policies, a `checkPolicies` method could be a transformation or an action.

`checkPolicies` returns a `CheckResult` object.

## Break things down

### Move some of the `SmvModule` method to `SmvDataSet` (type 1)
Unify `SmvFile` with `SmvModule`. The difference will mainly be the signature of the run method and requiresDS.

### Implement CheckResult and refine RejectLogger (type 1)
Implement `CheckResult`, `checkParserLogger`, `terminateAtError`, and check log persisting.

### Implement the dqm package (type 2)
