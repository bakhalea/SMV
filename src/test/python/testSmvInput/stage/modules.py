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

from smv import *
from smv.smvdataset import SmvInputFromFile

class Xml1(SmvXmlFile):
    def fullPath(self):
        return self.smvApp.inputDir() + '/' + 'xmltest/f1.xml'
    def rowTag(self):
        return 'ROW'

class Xml2(SmvXmlFile):
    def fullPath(self):
        return self.smvApp.inputDir() + '/' + 'xmltest/f1.xml'
    def fullSchemaPath(self):
        return self.smvApp.inputDir() + '/' + 'xmltest/f1.xml.json'
    def rowTag(self):
        return 'ROW'

class IFF1(SmvInputFromFile):
    def path(self):
        return "xmltest/f1.xml.gz"
    def readAsDF(self):
        pass