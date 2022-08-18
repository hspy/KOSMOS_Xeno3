import os, shutil
#from xml.dom import minidom

from POULibrary import POULibrary
#from OpcFileTreeNode import OPCFile

def GetLocalPath(filename):
    return os.path.join(os.path.split(__file__)[0], filename) 

class RootClass(POULibrary):
    def GetLibraryPath(self):
        return GetLocalPath("pous.xml")

    def Generate_C(self, buildpath, varlist, IECCFLAGS):
        c_file_path = os.path.join(os.path.split(__file__)[0], "HmiSock.c")
        c_file = open(c_file_path, 'r')
        c_code = c_file.read()
        c_file.close()

        #c_code = c_code % {"headers": Headers}

        gen_c_file_path = os.path.join(buildpath, "HmiSock.c")
        gen_c_file = open(gen_c_file_path,'w')
        gen_c_file.write(c_code)
        gen_c_file.close()

        return ((["hmisock"], [(gen_c_file_path, IECCFLAGS)], True),"")