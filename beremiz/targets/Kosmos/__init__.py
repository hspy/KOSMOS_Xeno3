from ..toolchain_gcc import toolchain_gcc

class Kosmos_target(toolchain_gcc):
    dlopen_prefix = "./"
    extension = ".so"
    def getXenoConfig(self, flagsname):
        """ Get xeno-config from target parameters """
        xeno_config=self.CTRInstance.GetTarget().getcontent()["value"].getXenoConfig()
        if xeno_config:
            from util.ProcessLogger import ProcessLogger
            status, result, err_result = ProcessLogger(self.CTRInstance.logger,
                                                       xeno_config + " --skin=native --"+flagsname,
                                                       no_stdout=True).spin()
            if status:
                self.CTRInstance.logger.write_error(_("Unable to get Kosmos's %s \n")%flagsname)
            return [result.strip()]
        return []
    
    def getBuilderLDFLAGS(self):
        xeno_ldflags = self.getXenoConfig("ldflags")
        return toolchain_gcc.getBuilderLDFLAGS(self) + xeno_ldflags + ["-shared"] + ["-L\"C:\Program Files (x86)\Beremiz\Kosmos\lib\""]

    def getBuilderCFLAGS(self):
        xeno_cflags = self.getXenoConfig("cflags")
        return toolchain_gcc.getBuilderCFLAGS(self) + xeno_cflags + ["-fPIC"] + ["-I\"C:\Program Files (x86)\Beremiz\Kosmos\include\""]
