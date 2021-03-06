name := "smv"

organization := "org.tresamigos"

version := "2-SNAPSHOT"

scalaVersion := "2.11.8"

scalacOptions ++= Seq("-deprecation", "-feature")

javacOptions ++= Seq("-source", "1.6", "-target", "1.6")

// Compile against earliest supported Spark - the jar will be foward compatible.
val sparkVersion = "2.1.0"

libraryDependencies ++= Seq(
  "org.apache.spark"             %% "spark-sql"         % sparkVersion % "provided",
  "org.apache.spark"             %% "spark-hive"        % sparkVersion % "provided",
  "org.scalatest"                %% "scalatest"         % "2.2.6"      % "test",
  "com.google.guava"             % "guava"              % "14.0.1",
  "org.rogach"                   %% "scallop"           % "0.9.5",
  "org.joda"                     % "joda-convert"       % "1.7",
  "joda-time"                    % "joda-time"          % "2.7",
  "com.rockymadden.stringmetric" %% "stringmetric-core" % "0.27.4",
  "com.databricks"               %% "spark-xml"         % "0.4.1"
)

parallelExecution in Test := false

publishArtifact in Test := true

testOptions in Test += Tests.Argument("-oF")

mainClass in assembly := Some("org.tresamigos.smv.SmvApp")

assemblyOption in assembly := (assemblyOption in assembly).value.copy(includeScala = false)

assemblyJarName in assembly := s"${name.value}-${version.value}-jar-with-dependencies.jar"

test in assembly := {}

// initialize ~= { _ => sys.props("scalac.patmat.analysisBudget") = "off" }
