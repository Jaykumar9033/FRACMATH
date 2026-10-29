# Windows compilation helper for the manuscript material examples.

def command_file(folder,driver,executable,extra=''):
    content='@echo off\n'+(
        'call "C:\\Program Files (x86)\\Intel\\oneAPI\\compiler\\2025.0\\env\\vars.bat" intel64 vs2022\n'
        'if errorlevel 1 exit /b 1\n'
        'ifx /O2 /extend-source /names:lowercase '
        '/include:"C:\\SIMULIA\\EstProducts\\2024\\SMAUsubs\\PublicInterfaces" '
        'cdm_umat_2d_OLIVER_T3_FAST.for '+extra+' '+driver+' /exe:'+executable+'\n'
        'if errorlevel 1 exit /b 1\n'+executable+'\n')
    # Normalize path separators in these Windows command arguments.
    content=content.replace('\\\\','\\')
    (folder/'compile_run.cmd').write_text(content,encoding='utf-8')
