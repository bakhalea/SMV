#
# This file is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

from test_support.smvbasetest import SmvBaseTest
from smv import SmvApp
from smv.datasetrepo import DataSetRepo

class ModuleHashTest(SmvBaseTest):
    @classmethod
    def smvAppInitArgs(cls):
        return ["--smv-props", "smv.stages=stage"]

    @classmethod
    def before_dir(cls):
        return cls.resourceTestDir() + "/before"

    @classmethod
    def after_dir(cls):
        return cls.resourceTestDir() + "/after"

    class Resource(object):
        def __init__(self, smvApp, path, fqn):
            # capture app dir on enter so we can set it back on exit
            self.initial_app_dir = smvApp.appDir()
            self.path = os.path.abspath(path)
            self.app = smvApp
            self.fqn = fqn

        def __enter__(self):
            self.app.setAppDir(self.path)
            print(self.app.appDir())
            self.app.SRC_PROJECT_PATH = "src/main/python"
            dsr = DataSetRepo(self.app)
            return dsr.loadDataSet(self.fqn)

        def __exit__(self, type, value, traceback):
            print('exit')
            # self.app.setAppDir

    def compare_resource_hash(self, fqn, assertion):
        with self.Resource(self.smvApp,self.before_dir(),fqn) as ds:
            hash1 = ds.sourceCodeHash()
        with self.Resource(self.smvApp,self.after_dir(),fqn) as ds:
            hash2 = ds.sourceCodeHash()
        assertion(hash1, hash2)

    def assert_hash_should_change(self, fqn):
        self.compare_resource_hash(fqn, self.assertNotEqual)

    def assert_hash_should_not_change(self, fqn):
        self.compare_resource_hash(fqn, self.assertEqual)

    def test_add_comment_should_not_change_hash(self):
        """hash will not change if we add a comment to its code"""
        self.assert_hash_should_not_change("stage.modules.AddComment")

    def test_change_code_should_change_hash(self):
        """hash will change if we change module's code"""
        self.assert_hash_should_change("stage.modules.ChangeCode")

    def test_change_dependency_should_change_hash(self):
        """hash will change if we change module's requiresDS"""
        self.assert_hash_should_change("stage.modules.Dependent")
    
    def test_unchanged_lib_same_hash(self):
        """verify that the same library source will produce the same hash"""
        self.assert_hash_should_not_change("stage.modules.SameLibrary")
    
    def test_change_required_lib_should_change_hash(self):
        """hash will change if we modify the source code of a depended-on library"""
        self.assert_hash_should_change("stage.modules.DifferentLibrary")
    
    def test_unchanged_func_same_hash(self):
        """verify hash is the same if a function in requiresLib is"""
        self.assert_hash_should_not_change("stage.modules.SameFunc")
    
    def test_change_func_should_change_hash(self):
        """verify that changing the source of a required function changes hash"""
        self.assert_hash_should_change("stage.modules.DifferentFunc")

    def test_change_baseclass_should_change_hash(self):
        """hash will change if we change code for class that module inherits from"""
        self.assert_hash_should_change("stage.modules.Child")

    def test_change_upstream_module_should_not_change_hash(self):
        """hash will not change if we change module that is listed in module's requiresDS"""
        self.assert_hash_should_not_change("stage.modules.Downstream")

    def test_change_hive_table_version_should_change_hash(self):
        """updating version of SmvHiveTable will force change of hash"""
        self.assert_hash_should_change("stage.modules.HiveTableWithVersion")

    def test_change_csv_file_run_method_should_change_hash(self):
        """updating run method of SmvCsvFile will change hash"""
        self.assert_hash_should_change("stage.modules.CsvFileWithRun")
