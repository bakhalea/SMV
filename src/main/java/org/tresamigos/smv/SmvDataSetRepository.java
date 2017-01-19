/*
 * This file is licensed under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.tresamigos.smv;

import java.util.List;
import java.util.Map;
import org.apache.spark.sql.DataFrame;
import org.tresamigos.smv.dqm.SmvDQM;
import org.tresamigos.smv.dqm.DQMValidator;

/**
 * Methods that can be implemented by a remote object, such as a
 * Python class, to allow modules written in different languages to
 * work together in an SMV application.
 */
public interface SmvDataSetRepository {
	/**
	 * Does the named data set exist?
	 */
	boolean hasDataSet(String modUrn);

	/**
	 * Factory method for ISmvModule
	 */
	ISmvModule getSmvModule(String modUrn);

	/**
	 * Does the named dataset need to be persisted?
	 *
	 * Input datasets and simple filter and map modules typically don't
	 * need to be persisted.
	 */
	boolean isEphemeral(String modUrn);

	/**
	 * The DQM policy attached to a named dataset.
	 */
	SmvDQM getDqm(String modUrn);

	/**
	 * A CSV of output module fqns for a stage.
	 */
	String outputModsForStage(String stageName);

	/**
	 * Dependent module fqns or an empty array.
	 *
	 * Python implementation of this method needs to return a Java array
	 * using the accompanying smv_copy_array() method.
	 */
	String[] dependencies(String modUrn);

	/**
	 * Try to run the module by its fully-qualified name and return its
	 * result in a DataFrame.
	 */
	DataFrame getDataFrame(String modUrn, DQMValidator validator,  Map<String, DataFrame> known);

	/**
	 * Re-run the named module after code change.
	 */
	DataFrame rerun(String modUrn, DQMValidator validator, Map<String, DataFrame> known);

	/**
	 * Calculate a hash for the named data set; can optionally include
	 * the hash for all its super classes up to and excluding the base
	 * class provided by SMV.
	 */
	int datasetHash(String modUrn, boolean includeSuperClass);
}
