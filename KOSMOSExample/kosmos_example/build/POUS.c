

void R_TRIG_init__(R_TRIG *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CLK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->M,__BOOL_LITERAL(FALSE),1)
}

// Code part
void R_TRIG_body__(R_TRIG *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,Q,(__GET_VAR(data__->CLK) && !(__GET_VAR(data__->M))));
  __SET_VAR(data__->,M,__GET_VAR(data__->CLK));

  goto __end;

__end:
  return;
} // R_TRIG_body__() 





void F_TRIG_init__(F_TRIG *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CLK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->M,__BOOL_LITERAL(FALSE),1)
}

// Code part
void F_TRIG_body__(F_TRIG *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,Q,(!(__GET_VAR(data__->CLK)) && !(__GET_VAR(data__->M))));
  __SET_VAR(data__->,M,!(__GET_VAR(data__->CLK)));

  goto __end;

__end:
  return;
} // F_TRIG_body__() 





void SR_init__(SR *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->S1,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->Q1,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void SR_body__(SR *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,Q1,(__GET_VAR(data__->S1) || (!(__GET_VAR(data__->R)) && __GET_VAR(data__->Q1))));

  goto __end;

__end:
  return;
} // SR_body__() 





void RS_init__(RS *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->S,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R1,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->Q1,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void RS_body__(RS *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,Q1,(!(__GET_VAR(data__->R1)) && (__GET_VAR(data__->S) || __GET_VAR(data__->Q1))));

  goto __end;

__end:
  return;
} // RS_body__() 





void CTU_init__(CTU *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTU_body__(CTU *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));

  goto __end;

__end:
  return;
} // CTU_body__() 





void CTU_DINT_init__(CTU_DINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTU_DINT_body__(CTU_DINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));

  goto __end;

__end:
  return;
} // CTU_DINT_body__() 





void CTU_LINT_init__(CTU_LINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTU_LINT_body__(CTU_LINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));

  goto __end;

__end:
  return;
} // CTU_LINT_body__() 





void CTU_UDINT_init__(CTU_UDINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTU_UDINT_body__(CTU_UDINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));

  goto __end;

__end:
  return;
} // CTU_UDINT_body__() 





void CTU_ULINT_init__(CTU_ULINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTU_ULINT_body__(CTU_ULINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));

  goto __end;

__end:
  return;
} // CTU_ULINT_body__() 





void CTD_init__(CTD *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
}

// Code part
void CTD_body__(CTD *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTD_body__() 





void CTD_DINT_init__(CTD_DINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
}

// Code part
void CTD_DINT_body__(CTD_DINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTD_DINT_body__() 





void CTD_LINT_init__(CTD_LINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
}

// Code part
void CTD_LINT_body__(CTD_LINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTD_LINT_body__() 





void CTD_UDINT_init__(CTD_UDINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
}

// Code part
void CTD_UDINT_body__(CTD_UDINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTD_UDINT_body__() 





void CTD_ULINT_init__(CTD_ULINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
}

// Code part
void CTD_ULINT_body__(CTD_ULINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
    __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTD_ULINT_body__() 





void CTUD_init__(CTUD *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->QU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->QD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTUD_body__(CTUD *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else {
    if (!((__GET_VAR(data__->CU_T.Q) && __GET_VAR(data__->CD_T.Q)))) {
      if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
      } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
      };
    };
  };
  __SET_VAR(data__->,QU,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));
  __SET_VAR(data__->,QD,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTUD_body__() 





void CTUD_DINT_init__(CTUD_DINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->QU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->QD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTUD_DINT_body__(CTUD_DINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else {
    if (!((__GET_VAR(data__->CU_T.Q) && __GET_VAR(data__->CD_T.Q)))) {
      if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
      } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
      };
    };
  };
  __SET_VAR(data__->,QU,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));
  __SET_VAR(data__->,QD,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTUD_DINT_body__() 





void CTUD_LINT_init__(CTUD_LINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->QU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->QD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTUD_LINT_body__(CTUD_LINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else {
    if (!((__GET_VAR(data__->CU_T.Q) && __GET_VAR(data__->CD_T.Q)))) {
      if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
      } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
      };
    };
  };
  __SET_VAR(data__->,QU,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));
  __SET_VAR(data__->,QD,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTUD_LINT_body__() 





void CTUD_UDINT_init__(CTUD_UDINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->QU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->QD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTUD_UDINT_body__(CTUD_UDINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else {
    if (!((__GET_VAR(data__->CU_T.Q) && __GET_VAR(data__->CD_T.Q)))) {
      if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
      } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
      };
    };
  };
  __SET_VAR(data__->,QU,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));
  __SET_VAR(data__->,QD,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTUD_UDINT_body__() 





void CTUD_ULINT_init__(CTUD_ULINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->LD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->QU,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->QD,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CV,0,retain)
  R_TRIG_init__(&data__->CD_T,retain);
  R_TRIG_init__(&data__->CU_T,retain);
}

// Code part
void CTUD_ULINT_body__(CTUD_ULINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->CD_T.,CLK,__GET_VAR(data__->CD));
  R_TRIG_body__(&data__->CD_T);
  __SET_VAR(data__->CU_T.,CLK,__GET_VAR(data__->CU));
  R_TRIG_body__(&data__->CU_T);
  if (__GET_VAR(data__->R)) {
    __SET_VAR(data__->,CV,0);
  } else if (__GET_VAR(data__->LD)) {
    __SET_VAR(data__->,CV,__GET_VAR(data__->PV));
  } else {
    if (!((__GET_VAR(data__->CU_T.Q) && __GET_VAR(data__->CD_T.Q)))) {
      if ((__GET_VAR(data__->CU_T.Q) && (__GET_VAR(data__->CV) < __GET_VAR(data__->PV)))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) + 1));
      } else if ((__GET_VAR(data__->CD_T.Q) && (__GET_VAR(data__->CV) > 0))) {
        __SET_VAR(data__->,CV,(__GET_VAR(data__->CV) - 1));
      };
    };
  };
  __SET_VAR(data__->,QU,(__GET_VAR(data__->CV) >= __GET_VAR(data__->PV)));
  __SET_VAR(data__->,QD,(__GET_VAR(data__->CV) <= 0));

  goto __end;

__end:
  return;
} // CTUD_ULINT_body__() 





void TP_init__(TP *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PT,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ET,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->STATE,0,retain)
  __INIT_VAR(data__->PREV_IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CURRENT_TIME,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->START_TIME,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
}

// Code part
void TP_body__(TP *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

    #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
  #define SetFbVar(var,val,...) __SET_VAR(data__->,var,val,__VA_ARGS__)
__SET_VAR(data__->,CURRENT_TIME,__CURRENT_TIME)
  #undef GetFbVar
  #undef SetFbVar
;
  if ((((__GET_VAR(data__->STATE) == 0) && !(__GET_VAR(data__->PREV_IN))) && __GET_VAR(data__->IN))) {
    __SET_VAR(data__->,STATE,1);
    __SET_VAR(data__->,Q,__BOOL_LITERAL(TRUE));
    __SET_VAR(data__->,START_TIME,__GET_VAR(data__->CURRENT_TIME));
  } else if ((__GET_VAR(data__->STATE) == 1)) {
    if (LE_TIME(__BOOL_LITERAL(TRUE), NULL, 2, __time_add(__GET_VAR(data__->START_TIME), __GET_VAR(data__->PT)), __GET_VAR(data__->CURRENT_TIME))) {
      __SET_VAR(data__->,STATE,2);
      __SET_VAR(data__->,Q,__BOOL_LITERAL(FALSE));
      __SET_VAR(data__->,ET,__GET_VAR(data__->PT));
    } else {
      __SET_VAR(data__->,ET,__time_sub(__GET_VAR(data__->CURRENT_TIME), __GET_VAR(data__->START_TIME)));
    };
  };
  if (((__GET_VAR(data__->STATE) == 2) && !(__GET_VAR(data__->IN)))) {
    __SET_VAR(data__->,ET,__time_to_timespec(1, 0, 0, 0, 0, 0));
    __SET_VAR(data__->,STATE,0);
  };
  __SET_VAR(data__->,PREV_IN,__GET_VAR(data__->IN));

  goto __end;

__end:
  return;
} // TP_body__() 





void TON_init__(TON *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PT,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ET,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->STATE,0,retain)
  __INIT_VAR(data__->PREV_IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CURRENT_TIME,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->START_TIME,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
}

// Code part
void TON_body__(TON *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

    #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
  #define SetFbVar(var,val,...) __SET_VAR(data__->,var,val,__VA_ARGS__)
__SET_VAR(data__->,CURRENT_TIME,__CURRENT_TIME)
  #undef GetFbVar
  #undef SetFbVar
;
  if ((((__GET_VAR(data__->STATE) == 0) && !(__GET_VAR(data__->PREV_IN))) && __GET_VAR(data__->IN))) {
    __SET_VAR(data__->,STATE,1);
    __SET_VAR(data__->,Q,__BOOL_LITERAL(FALSE));
    __SET_VAR(data__->,START_TIME,__GET_VAR(data__->CURRENT_TIME));
  } else {
    if (!(__GET_VAR(data__->IN))) {
      __SET_VAR(data__->,ET,__time_to_timespec(1, 0, 0, 0, 0, 0));
      __SET_VAR(data__->,Q,__BOOL_LITERAL(FALSE));
      __SET_VAR(data__->,STATE,0);
    } else if ((__GET_VAR(data__->STATE) == 1)) {
      if (LE_TIME(__BOOL_LITERAL(TRUE), NULL, 2, __time_add(__GET_VAR(data__->START_TIME), __GET_VAR(data__->PT)), __GET_VAR(data__->CURRENT_TIME))) {
        __SET_VAR(data__->,STATE,2);
        __SET_VAR(data__->,Q,__BOOL_LITERAL(TRUE));
        __SET_VAR(data__->,ET,__GET_VAR(data__->PT));
      } else {
        __SET_VAR(data__->,ET,__time_sub(__GET_VAR(data__->CURRENT_TIME), __GET_VAR(data__->START_TIME)));
      };
    };
  };
  __SET_VAR(data__->,PREV_IN,__GET_VAR(data__->IN));

  goto __end;

__end:
  return;
} // TON_body__() 





void TOF_init__(TOF *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PT,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ET,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->STATE,0,retain)
  __INIT_VAR(data__->PREV_IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CURRENT_TIME,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->START_TIME,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
}

// Code part
void TOF_body__(TOF *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

    #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
  #define SetFbVar(var,val,...) __SET_VAR(data__->,var,val,__VA_ARGS__)
__SET_VAR(data__->,CURRENT_TIME,__CURRENT_TIME)
  #undef GetFbVar
  #undef SetFbVar
;
  if ((((__GET_VAR(data__->STATE) == 0) && __GET_VAR(data__->PREV_IN)) && !(__GET_VAR(data__->IN)))) {
    __SET_VAR(data__->,STATE,1);
    __SET_VAR(data__->,START_TIME,__GET_VAR(data__->CURRENT_TIME));
  } else {
    if (__GET_VAR(data__->IN)) {
      __SET_VAR(data__->,ET,__time_to_timespec(1, 0, 0, 0, 0, 0));
      __SET_VAR(data__->,STATE,0);
    } else if ((__GET_VAR(data__->STATE) == 1)) {
      if (LE_TIME(__BOOL_LITERAL(TRUE), NULL, 2, __time_add(__GET_VAR(data__->START_TIME), __GET_VAR(data__->PT)), __GET_VAR(data__->CURRENT_TIME))) {
        __SET_VAR(data__->,STATE,2);
        __SET_VAR(data__->,ET,__GET_VAR(data__->PT));
      } else {
        __SET_VAR(data__->,ET,__time_sub(__GET_VAR(data__->CURRENT_TIME), __GET_VAR(data__->START_TIME)));
      };
    };
  };
  __SET_VAR(data__->,Q,(__GET_VAR(data__->IN) || (__GET_VAR(data__->STATE) == 1)));
  __SET_VAR(data__->,PREV_IN,__GET_VAR(data__->IN));

  goto __end;

__end:
  return;
} // TOF_body__() 





void DERIVATIVE_init__(DERIVATIVE *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->RUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->XIN,0,retain)
  __INIT_VAR(data__->CYCLE,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->XOUT,0,retain)
  __INIT_VAR(data__->X1,0,retain)
  __INIT_VAR(data__->X2,0,retain)
  __INIT_VAR(data__->X3,0,retain)
}

// Code part
void DERIVATIVE_body__(DERIVATIVE *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if (__GET_VAR(data__->RUN)) {
    __SET_VAR(data__->,XOUT,((((3.0 * (__GET_VAR(data__->XIN) - __GET_VAR(data__->X3))) + __GET_VAR(data__->X1)) - __GET_VAR(data__->X2)) / (10.0 * TIME_TO_REAL((BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (TIME)__GET_VAR(data__->CYCLE)))));
    __SET_VAR(data__->,X3,__GET_VAR(data__->X2));
    __SET_VAR(data__->,X2,__GET_VAR(data__->X1));
    __SET_VAR(data__->,X1,__GET_VAR(data__->XIN));
  } else {
    __SET_VAR(data__->,XOUT,0.0);
    __SET_VAR(data__->,X1,__GET_VAR(data__->XIN));
    __SET_VAR(data__->,X2,__GET_VAR(data__->XIN));
    __SET_VAR(data__->,X3,__GET_VAR(data__->XIN));
  };

  goto __end;

__end:
  return;
} // DERIVATIVE_body__() 





void HYSTERESIS_init__(HYSTERESIS *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->XIN1,0,retain)
  __INIT_VAR(data__->XIN2,0,retain)
  __INIT_VAR(data__->EPS,0,retain)
  __INIT_VAR(data__->Q,0,retain)
}

// Code part
void HYSTERESIS_body__(HYSTERESIS *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if (__GET_VAR(data__->Q)) {
    if ((__GET_VAR(data__->XIN1) < (__GET_VAR(data__->XIN2) - __GET_VAR(data__->EPS)))) {
      __SET_VAR(data__->,Q,0);
    };
  } else if ((__GET_VAR(data__->XIN1) > (__GET_VAR(data__->XIN2) + __GET_VAR(data__->EPS)))) {
    __SET_VAR(data__->,Q,1);
  };

  goto __end;

__end:
  return;
} // HYSTERESIS_body__() 





void INTEGRAL_init__(INTEGRAL *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->RUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->R1,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->XIN,0,retain)
  __INIT_VAR(data__->X0,0,retain)
  __INIT_VAR(data__->CYCLE,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->XOUT,0,retain)
}

// Code part
void INTEGRAL_body__(INTEGRAL *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,Q,!(__GET_VAR(data__->R1)));
  if (__GET_VAR(data__->R1)) {
    __SET_VAR(data__->,XOUT,__GET_VAR(data__->X0));
  } else if (__GET_VAR(data__->RUN)) {
    __SET_VAR(data__->,XOUT,(__GET_VAR(data__->XOUT) + (__GET_VAR(data__->XIN) * TIME_TO_REAL((BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (TIME)__GET_VAR(data__->CYCLE)))));
  };

  goto __end;

__end:
  return;
} // INTEGRAL_body__() 





void PID_init__(PID *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->AUTO,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PV,0,retain)
  __INIT_VAR(data__->SP,0,retain)
  __INIT_VAR(data__->X0,0,retain)
  __INIT_VAR(data__->KP,0,retain)
  __INIT_VAR(data__->TR,0,retain)
  __INIT_VAR(data__->TD,0,retain)
  __INIT_VAR(data__->CYCLE,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->XOUT,0,retain)
  __INIT_VAR(data__->ERROR,0,retain)
  INTEGRAL_init__(&data__->ITERM,retain);
  DERIVATIVE_init__(&data__->DTERM,retain);
}

// Code part
void PID_body__(PID *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,ERROR,(__GET_VAR(data__->PV) - __GET_VAR(data__->SP)));
  __SET_VAR(data__->ITERM.,RUN,__GET_VAR(data__->AUTO));
  __SET_VAR(data__->ITERM.,R1,!(__GET_VAR(data__->AUTO)));
  __SET_VAR(data__->ITERM.,XIN,__GET_VAR(data__->ERROR));
  __SET_VAR(data__->ITERM.,X0,(__GET_VAR(data__->TR) * (__GET_VAR(data__->X0) - __GET_VAR(data__->ERROR))));
  __SET_VAR(data__->ITERM.,CYCLE,__GET_VAR(data__->CYCLE));
  INTEGRAL_body__(&data__->ITERM);
  __SET_VAR(data__->DTERM.,RUN,__GET_VAR(data__->AUTO));
  __SET_VAR(data__->DTERM.,XIN,__GET_VAR(data__->ERROR));
  __SET_VAR(data__->DTERM.,CYCLE,__GET_VAR(data__->CYCLE));
  DERIVATIVE_body__(&data__->DTERM);
  __SET_VAR(data__->,XOUT,(__GET_VAR(data__->KP) * ((__GET_VAR(data__->ERROR) + (__GET_VAR(data__->ITERM.XOUT) / __GET_VAR(data__->TR))) + (__GET_VAR(data__->DTERM.XOUT) * __GET_VAR(data__->TD)))));

  goto __end;

__end:
  return;
} // PID_body__() 





void RAMP_init__(RAMP *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->RUN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->X0,0,retain)
  __INIT_VAR(data__->X1,0,retain)
  __INIT_VAR(data__->TR,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->CYCLE,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->BUSY,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->XOUT,0.0,retain)
  __INIT_VAR(data__->XI,0,retain)
  __INIT_VAR(data__->T,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
}

// Code part
void RAMP_body__(RAMP *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,BUSY,__GET_VAR(data__->RUN));
  if (__GET_VAR(data__->RUN)) {
    if (GE_TIME(__BOOL_LITERAL(TRUE), NULL, 2, __GET_VAR(data__->T), __GET_VAR(data__->TR))) {
      __SET_VAR(data__->,BUSY,0);
      __SET_VAR(data__->,XOUT,__GET_VAR(data__->X1));
    } else {
      __SET_VAR(data__->,XOUT,(__GET_VAR(data__->XI) + (((__GET_VAR(data__->X1) - __GET_VAR(data__->XI)) * TIME_TO_REAL((BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (TIME)__GET_VAR(data__->T))) / TIME_TO_REAL((BOOL)__BOOL_LITERAL(TRUE),
        NULL,
        (TIME)__GET_VAR(data__->TR)))));
      __SET_VAR(data__->,T,__time_add(__GET_VAR(data__->T), __GET_VAR(data__->CYCLE)));
    };
  } else {
    __SET_VAR(data__->,XOUT,__GET_VAR(data__->X0));
    __SET_VAR(data__->,XI,__GET_VAR(data__->X0));
    __SET_VAR(data__->,T,__time_to_timespec(1, 0, 0, 0, 0, 0));
  };

  goto __end;

__end:
  return;
} // RAMP_body__() 





void RTC_init__(RTC *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PDT,__dt_to_timespec(0, 0, 0, 1, 1, 1970),retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CDT,__dt_to_timespec(0, 0, 0, 1, 1, 1970),retain)
  __INIT_VAR(data__->PREV_IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OFFSET,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->CURRENT_TIME,__dt_to_timespec(0, 0, 0, 1, 1, 1970),retain)
}

// Code part
void RTC_body__(RTC *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

    #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
  #define SetFbVar(var,val,...) __SET_VAR(data__->,var,val,__VA_ARGS__)
__SET_VAR(data__->,CURRENT_TIME,__CURRENT_TIME)
  #undef GetFbVar
  #undef SetFbVar
;
  if (__GET_VAR(data__->IN)) {
    if (!(__GET_VAR(data__->PREV_IN))) {
      __SET_VAR(data__->,OFFSET,__time_sub(__GET_VAR(data__->PDT), __GET_VAR(data__->CURRENT_TIME)));
    };
    __SET_VAR(data__->,CDT,__time_add(__GET_VAR(data__->CURRENT_TIME), __GET_VAR(data__->OFFSET)));
  } else {
    __SET_VAR(data__->,CDT,__GET_VAR(data__->CURRENT_TIME));
  };
  __SET_VAR(data__->,Q,__GET_VAR(data__->IN));
  __SET_VAR(data__->,PREV_IN,__GET_VAR(data__->IN));

  goto __end;

__end:
  return;
} // RTC_body__() 





void SEMA_init__(SEMA *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CLAIM,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RELEASE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->BUSY,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->Q_INTERNAL,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void SEMA_body__(SEMA *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,Q_INTERNAL,(__GET_VAR(data__->CLAIM) || (__GET_VAR(data__->Q_INTERNAL) && !(__GET_VAR(data__->RELEASE)))));
  __SET_VAR(data__->,BUSY,__GET_VAR(data__->Q_INTERNAL));

  goto __end;

__end:
  return;
} // SEMA_body__() 





void LOGGER_init__(LOGGER *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->TRIG,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MSG,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->LEVEL,LOGLEVEL__INFO,retain)
  __INIT_VAR(data__->TRIG0,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void LOGGER_body__(LOGGER *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_VAR(data__->TRIG) && !(__GET_VAR(data__->TRIG0)))) {
        #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
    #define SetFbVar(var,val,...) __SET_VAR(data__->,var,val,__VA_ARGS__)

   LogMessage(GetFbVar(LEVEL),(char*)GetFbVar(MSG, .body),GetFbVar(MSG, .len));
  
    #undef GetFbVar
    #undef SetFbVar
;
  };
  __SET_VAR(data__->,TRIG0,__GET_VAR(data__->TRIG));

  goto __end;

__end:
  return;
} // LOGGER_body__() 





void PYTHON_EVAL_init__(PYTHON_EVAL *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->TRIG,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CODE,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->ACK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RESULT,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->STATE,0,retain)
  __INIT_VAR(data__->BUFFER,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->PREBUFFER,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->TRIGM1,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->TRIGGED,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void PYTHON_EVAL_body__(PYTHON_EVAL *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

    #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
  #define SetFbVar(var,val,...) __SET_VAR(data__->,var,val,__VA_ARGS__)
extern void __PythonEvalFB(int, PYTHON_EVAL*);__PythonEvalFB(0, data__);
  #undef GetFbVar
  #undef SetFbVar
;

  goto __end;

__end:
  return;
} // PYTHON_EVAL_body__() 





void PYTHON_POLL_init__(PYTHON_POLL *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->TRIG,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CODE,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->ACK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RESULT,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->STATE,0,retain)
  __INIT_VAR(data__->BUFFER,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->PREBUFFER,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->TRIGM1,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->TRIGGED,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void PYTHON_POLL_body__(PYTHON_POLL *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

    #define GetFbVar(var,...) __GET_VAR(data__->var,__VA_ARGS__)
  #define SetFbVar(var,val,...) __SET_VAR(data__->,var,val,__VA_ARGS__)
extern void __PythonEvalFB(int, PYTHON_EVAL*);__PythonEvalFB(1,(PYTHON_EVAL*)(void*)data__);
  #undef GetFbVar
  #undef SetFbVar
;

  goto __end;

__end:
  return;
} // PYTHON_POLL_body__() 





void PYTHON_GEAR_init__(PYTHON_GEAR *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->N,0,retain)
  __INIT_VAR(data__->TRIG,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CODE,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->ACK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->RESULT,__STRING_LITERAL(0,""),retain)
  PYTHON_EVAL_init__(&data__->PY_EVAL,retain);
  __INIT_VAR(data__->COUNTER,0,retain)
  __INIT_VAR(data__->ADD10_OUT,0,retain)
  __INIT_VAR(data__->EQ13_OUT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SEL15_OUT,0,retain)
  __INIT_VAR(data__->AND7_OUT,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void PYTHON_GEAR_body__(PYTHON_GEAR *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,ADD10_OUT,ADD__USINT__USINT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (USINT)__GET_VAR(data__->COUNTER),
    (USINT)__USINT_LITERAL(1)));
  __SET_VAR(data__->,EQ13_OUT,EQ__BOOL__USINT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (USINT)__GET_VAR(data__->N),
    (USINT)__GET_VAR(data__->ADD10_OUT)));
  __SET_VAR(data__->,SEL15_OUT,SEL__USINT__BOOL__USINT__USINT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (BOOL)__GET_VAR(data__->EQ13_OUT),
    (USINT)__GET_VAR(data__->ADD10_OUT),
    (USINT)__USINT_LITERAL(0)));
  __SET_VAR(data__->,COUNTER,__GET_VAR(data__->SEL15_OUT));
  __SET_VAR(data__->,AND7_OUT,AND__BOOL__BOOL((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (BOOL)__GET_VAR(data__->EQ13_OUT),
    (BOOL)__GET_VAR(data__->TRIG)));
  __SET_VAR(data__->PY_EVAL.,TRIG,__GET_VAR(data__->AND7_OUT));
  __SET_VAR(data__->PY_EVAL.,CODE,__GET_VAR(data__->CODE));
  PYTHON_EVAL_body__(&data__->PY_EVAL);
  __SET_VAR(data__->,ACK,__GET_VAR(data__->PY_EVAL.ACK));
  __SET_VAR(data__->,RESULT,__GET_VAR(data__->PY_EVAL.RESULT));

  goto __end;

__end:
  return;
} // PYTHON_GEAR_body__() 





void GETBOOLSTRING_init__(GETBOOLSTRING *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->VALUE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CODE,__STRING_LITERAL(0,""),retain)
}

// Code part
void GETBOOLSTRING_body__(GETBOOLSTRING *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if (__GET_VAR(data__->VALUE)) {
    __SET_VAR(data__->,CODE,__STRING_LITERAL(4,"True"));
  } else {
    __SET_VAR(data__->,CODE,__STRING_LITERAL(5,"False"));
  };

  goto __end;

__end:
  return;
} // GETBOOLSTRING_body__() 





void BUTTON_init__(BUTTON *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ID,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->BACK_ID,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->SELE_ID,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->TOGGLE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->SET_STATE,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATE_IN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STATE_OUT,__BOOL_LITERAL(FALSE),retain)
  PYTHON_EVAL_init__(&data__->INIT_COMMAND,retain);
  GETBOOLSTRING_init__(&data__->GETBUTTONSTATE,retain);
  PYTHON_EVAL_init__(&data__->SETSTATE_COMMAND,retain);
  PYTHON_POLL_init__(&data__->GETSTATE_COMMAND,retain);
  GETBOOLSTRING_init__(&data__->GETBUTTONTOGGLE,retain);
  __INIT_VAR(data__->CONCAT2_OUT,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->CONCAT22_OUT,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->STRING_TO_INT25_OUT,0,retain)
  __INIT_VAR(data__->INT_TO_BOOL26_OUT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AND31_OUT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CONCAT7_OUT,__STRING_LITERAL(0,""),retain)
}

// Code part
void BUTTON_body__(BUTTON *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->GETBUTTONTOGGLE.,VALUE,__GET_VAR(data__->TOGGLE));
  GETBOOLSTRING_body__(&data__->GETBUTTONTOGGLE);
  __SET_VAR(data__->,CONCAT2_OUT,CONCAT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)7,
    (STRING)__STRING_LITERAL(37,"createSVGUIControl(\"button\",back_id=\""),
    (STRING)__GET_VAR(data__->BACK_ID),
    (STRING)__STRING_LITERAL(11,"\",sele_id=\""),
    (STRING)__GET_VAR(data__->SELE_ID),
    (STRING)__STRING_LITERAL(9,"\",toggle="),
    (STRING)__GET_VAR(data__->GETBUTTONTOGGLE.CODE),
    (STRING)__STRING_LITERAL(13,",active=True)")));
  __SET_VAR(data__->INIT_COMMAND.,TRIG,__BOOL_LITERAL(TRUE));
  __SET_VAR(data__->INIT_COMMAND.,CODE,__GET_VAR(data__->CONCAT2_OUT));
  PYTHON_EVAL_body__(&data__->INIT_COMMAND);
  __SET_VAR(data__->,ID,__GET_VAR(data__->INIT_COMMAND.RESULT));
  __SET_VAR(data__->,CONCAT22_OUT,CONCAT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)3,
    (STRING)__STRING_LITERAL(12,"int(getAttr("),
    (STRING)__GET_VAR(data__->ID),
    (STRING)__STRING_LITERAL(16,",\"state\",False))")));
  __SET_VAR(data__->GETSTATE_COMMAND.,TRIG,__GET_VAR(data__->INIT_COMMAND.ACK));
  __SET_VAR(data__->GETSTATE_COMMAND.,CODE,__GET_VAR(data__->CONCAT22_OUT));
  PYTHON_POLL_body__(&data__->GETSTATE_COMMAND);
  __SET_VAR(data__->,STRING_TO_INT25_OUT,STRING_TO_INT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (STRING)__GET_VAR(data__->GETSTATE_COMMAND.RESULT)));
  __SET_VAR(data__->,INT_TO_BOOL26_OUT,INT_TO_BOOL((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (INT)__GET_VAR(data__->STRING_TO_INT25_OUT)));
  __SET_VAR(data__->,STATE_OUT,__GET_VAR(data__->INT_TO_BOOL26_OUT));
  __SET_VAR(data__->,AND31_OUT,AND__BOOL__BOOL((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (BOOL)__GET_VAR(data__->INIT_COMMAND.ACK),
    (BOOL)__GET_VAR(data__->SET_STATE)));
  __SET_VAR(data__->GETBUTTONSTATE.,VALUE,__GET_VAR(data__->STATE_IN));
  GETBOOLSTRING_body__(&data__->GETBUTTONSTATE);
  __SET_VAR(data__->,CONCAT7_OUT,CONCAT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)5,
    (STRING)__STRING_LITERAL(8,"setAttr("),
    (STRING)__GET_VAR(data__->ID),
    (STRING)__STRING_LITERAL(9,",\"state\","),
    (STRING)__GET_VAR(data__->GETBUTTONSTATE.CODE),
    (STRING)__STRING_LITERAL(1,")")));
  __SET_VAR(data__->SETSTATE_COMMAND.,TRIG,__GET_VAR(data__->AND31_OUT));
  __SET_VAR(data__->SETSTATE_COMMAND.,CODE,__GET_VAR(data__->CONCAT7_OUT));
  PYTHON_EVAL_body__(&data__->SETSTATE_COMMAND);

  goto __end;

__end:
  return;
} // BUTTON_body__() 





void LED_init__(LED *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ID,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->BACK_ID,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->SELE_ID,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->STATE_IN,__BOOL_LITERAL(FALSE),retain)
  PYTHON_EVAL_init__(&data__->INIT_COMMAND,retain);
  PYTHON_POLL_init__(&data__->SETSTATE_COMMAND,retain);
  GETBOOLSTRING_init__(&data__->GETLEDSTATE,retain);
  __INIT_VAR(data__->CONCAT2_OUT,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->CONCAT7_OUT,__STRING_LITERAL(0,""),retain)
}

// Code part
void LED_body__(LED *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,CONCAT2_OUT,CONCAT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)5,
    (STRING)__STRING_LITERAL(37,"createSVGUIControl(\"button\",back_id=\""),
    (STRING)__GET_VAR(data__->BACK_ID),
    (STRING)__STRING_LITERAL(11,"\",sele_id=\""),
    (STRING)__GET_VAR(data__->SELE_ID),
    (STRING)__STRING_LITERAL(27,"\",toggle=True,active=False)")));
  __SET_VAR(data__->INIT_COMMAND.,TRIG,__BOOL_LITERAL(TRUE));
  __SET_VAR(data__->INIT_COMMAND.,CODE,__GET_VAR(data__->CONCAT2_OUT));
  PYTHON_EVAL_body__(&data__->INIT_COMMAND);
  __SET_VAR(data__->,ID,__GET_VAR(data__->INIT_COMMAND.RESULT));
  __SET_VAR(data__->GETLEDSTATE.,VALUE,__GET_VAR(data__->STATE_IN));
  GETBOOLSTRING_body__(&data__->GETLEDSTATE);
  __SET_VAR(data__->,CONCAT7_OUT,CONCAT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)5,
    (STRING)__STRING_LITERAL(8,"setAttr("),
    (STRING)__GET_VAR(data__->ID),
    (STRING)__STRING_LITERAL(9,",\"state\","),
    (STRING)__GET_VAR(data__->GETLEDSTATE.CODE),
    (STRING)__STRING_LITERAL(1,")")));
  __SET_VAR(data__->SETSTATE_COMMAND.,TRIG,__GET_VAR(data__->INIT_COMMAND.ACK));
  __SET_VAR(data__->SETSTATE_COMMAND.,CODE,__GET_VAR(data__->CONCAT7_OUT));
  PYTHON_POLL_body__(&data__->SETSTATE_COMMAND);

  goto __end;

__end:
  return;
} // LED_body__() 





void TEXTCTRL_init__(TEXTCTRL *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ID,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->BACK_ID,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->SET_TEXT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->TEXT,__STRING_LITERAL(0,""),retain)
  PYTHON_EVAL_init__(&data__->SVGUI_TEXTCTRL,retain);
  PYTHON_EVAL_init__(&data__->SETSTATE_COMMAND,retain);
  __INIT_VAR(data__->CONCAT1_OUT,__STRING_LITERAL(0,""),retain)
  __INIT_VAR(data__->AND31_OUT,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CONCAT12_OUT,__STRING_LITERAL(0,""),retain)
}

// Code part
void TEXTCTRL_body__(TEXTCTRL *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,CONCAT1_OUT,CONCAT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)3,
    (STRING)__STRING_LITERAL(43,"createSVGUIControl(\"textControl\", back_id=\""),
    (STRING)__GET_VAR(data__->BACK_ID),
    (STRING)__STRING_LITERAL(2,"\")")));
  __SET_VAR(data__->SVGUI_TEXTCTRL.,TRIG,__BOOL_LITERAL(TRUE));
  __SET_VAR(data__->SVGUI_TEXTCTRL.,CODE,__GET_VAR(data__->CONCAT1_OUT));
  PYTHON_EVAL_body__(&data__->SVGUI_TEXTCTRL);
  __SET_VAR(data__->,ID,__GET_VAR(data__->SVGUI_TEXTCTRL.RESULT));
  __SET_VAR(data__->,AND31_OUT,AND__BOOL__BOOL((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (BOOL)__GET_VAR(data__->SVGUI_TEXTCTRL.ACK),
    (BOOL)__GET_VAR(data__->SET_TEXT)));
  __SET_VAR(data__->,CONCAT12_OUT,CONCAT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)5,
    (STRING)__STRING_LITERAL(8,"setAttr("),
    (STRING)__GET_VAR(data__->ID),
    (STRING)__STRING_LITERAL(9,",\"text\",\""),
    (STRING)__GET_VAR(data__->TEXT),
    (STRING)__STRING_LITERAL(2,"\")")));
  __SET_VAR(data__->SETSTATE_COMMAND.,TRIG,__GET_VAR(data__->AND31_OUT));
  __SET_VAR(data__->SETSTATE_COMMAND.,CODE,__GET_VAR(data__->CONCAT12_OUT));
  PYTHON_EVAL_body__(&data__->SETSTATE_COMMAND);

  goto __end;

__end:
  return;
} // TEXTCTRL_body__() 





void PROGRAM0_init__(PROGRAM0 *data__, BOOL retain) {
  __INIT_VAR(data__->LOCALVAR0,0,retain)
  __INIT_VAR(data__->ADD1_OUT,0,retain)
}

// Code part
void PROGRAM0_body__(PROGRAM0 *data__) {
  // Initialise TEMP variables

  __SET_VAR(data__->,ADD1_OUT,ADD__INT__INT((BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (INT)__GET_VAR(data__->LOCALVAR0),
    (INT)1));
  __SET_VAR(data__->,LOCALVAR0,__GET_VAR(data__->ADD1_OUT));

  goto __end;

__end:
  return;
} // PROGRAM0_body__() 





