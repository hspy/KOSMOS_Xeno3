PROGRAM program0
  VAR
    LocalVar0 : INT;
    ADD1_OUT : INT;
  END_VAR

  ADD1_OUT := ADD(LocalVar0, 1);
  LocalVar0 := ADD1_OUT;
END_PROGRAM


CONFIGURATION config

  RESOURCE resource1 ON PLC
    TASK task_1(INTERVAL := T#1ms,PRIORITY := 0);
    PROGRAM inst_1 WITH task_1 : program0;
  END_RESOURCE
END_CONFIGURATION
