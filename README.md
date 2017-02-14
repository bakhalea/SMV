# Spark Modularized View (SMV)
Spark Modularized View enables users to build enterprise scale applications on Apache Spark platform.

## Why SMV
* Scales with **DATA** size
* Scales with **CODE** size
* Scales with **TEAM** size

In addition to the data scalability inherited from Spark, SMV also provides code and team scalability through
the following features:
* Multi-level modular design allow developers to work on large scale projects, and enable easy code and data reuse
* Multi-grain traceability to support full scope knowledge transparency to developers and data users
* Provides interfaces to multiple languages(Scala and R for now) for easy integrating to existing code and leverage existing developer experiences
* Pure text code, can utilized modern CM (Configuration Management) tool to track and merge changes among team members
* Automatic Data and Code version synchronization to enable coordination on both code and data level
* Data publishing mechanism to support inter-team coordination
* Build-in data quality management to ensure data quality in a continuous bases
* High level helper functions and tools for quick data App development

Please refer to [User Guide](docs/user/0_user_toc.md) and
[API docs](http://tresamigossd.github.io/SMV/scaladocs/index.html#org.tresamigos.smv.package) for details.

:cherries::cherries: Please see [***Important Announcment***](docs/announcement.md) for latest update which may impact users' projects or scripts.

**Note:** The sections below were extracted from the User Guide and it should be consulted for more detailed instructions.

# Quick links
* [Installation Guide](docs/installation.md)
* [Getting Started](#env)
* [User Guide](docs/0_user_toc.md)
* [API docs](http://tresamigossd.github.io/SMV/scaladocs/index.html#org.tresamigos.smv.package)


<a href='env'>
# SMV Getting Started

## Installation

We avidly recommend using [Docker](https://docs.docker.com/engine/installation/) to install SMV. Using Docker, start an SMV container with

```
docker run -it --rm tresamigos/smv
```

If Docker is not an option on your system, see the [installation guide](docs/installation.md).

## Create example App

SMV provides a shell script to easily create template applications. We will use a simple example app to explore SMV.

```shell
$ smv-init -s MyApp
```

## Run Example App

Run the entire application with

```shell
$ smv-pyrun --run-app
```

The output csv file and schema can be found in the `data/output` directory

```shell
$ cat data/output/com.mycompany.myapp.stage1.EmploymentByState_XXXXXXXX.csv/part-* | head -5
"50",245058
"51",2933665
"53",2310426
"54",531834
"55",2325877

$ cat data/output/com.mycompany.myapp.stage1.EmploymentByState_XXXXXXXX.schema/part-*
@delimiter = ,
@has-header = false
@quote-char = "
ST: String[,_SmvStrNull_]
EMP: Long
```

## Add an aggregation

The `EmploymentByState` module is defined in `src/python/com/mycompany/myapp/employment.py`:

```shell
class EmploymentByState(SmvPyModule, SmvPyOutput):
    """Python ETL Example: employment by state"""

    def requiresDS(self):
        return [inputdata.Employment]

    def run(self, i):
        df = i[inputdata.Employment]
        df1 = df.groupBy(col("ST")).agg(sum(col("EMP")).alias("EMP"))
        return df1
```

The `run` method of a module defines the operations needed to get the output based on the input. We would like to add a column describing whether or not employment number in each row's state is greater or less than 1,000,000. To accomplish this, we need to add an aggregation to the `run` method:

```shell
  def run(self, i):
      df = i[inputdata.Employment]
      df1 = df.groupBy(col("ST")).agg(sum(col("EMP")).alias("EMP"))
      df2 = df1.smvSelectPlus((col("EMP") > lit(1000000)).alias("cat_high_emp"))
      return df2
```

Now inspect the output again:

```shell
$ cat data/output/com.mycompany.myapp.EmploymentByState_XXXXXXXX.csv/part-* | head -5
"50",245058,false
"51",2933665,true
"53",2310426,true
"54",531834,false
"55",2325877,true

$ cat data/output/com.mycompany.myapp.EmploymentByState_XXXXXXXX.schema/part-*
@delimiter = ,
@has-header = false
@quote-char = "
ST: String[,_SmvStrNull_]
EMP: Long
cat_high_emp: Boolean
```

## smv-pyshell

We can also view the results in the smv-pyshell. To start the shell, run

```
$ smv-pyshell
```

To get the `DataFrame` of `EmploymentByState`,

```shell
>>> x = df('com.mycompany.myapp.stage1.EmploymentByState')

```

To peek at the first row of results,

```shell
>>> x.peek(1)
ST:String            = 50
EMP:Long             = 245058
cat_high_emp:Boolean = false
```

See the [user guide](docs/0_user_toc.md) for further examples and documentation.
