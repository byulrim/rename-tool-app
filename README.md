# rename-tool-app

사용 예시(Windows PowerShell에서 빈 문자열 replacement 전달하기)

PowerShell은 빈 문자열 인자를 직접 전달할 때 인자 누락이 발생할 수 있습니다. 아래 두 가지 방법을 권장합니다.

1) PowerShell 변수에 빈 문자열을 담아 전달
```powershell
$empty = ''
& .\.venv\Scripts\python.exe .\src\rename_with_dirs.py 'aa - ' $empty --rename-dirs
```

2) cmd를 통해 전달 (PowerShell에서 cmd 구문을 통해 빈 문자열 전달)
```powershell
cmd /c ""D:\Workspaces\rename-tool-app\.venv\Scripts\python.exe" "D:\Workspaces\rename-tool-app\src\rename_with_dirs.py" "aa - " "" "D:\Workspaces\rename-tool-app" --rename-dirs"
```

또는 저장소에 스크립트가 있습니다: `scripts/run_via_cmd.ps1` 를 사용하면 간단하게 호출할 수 있습니다:
```powershell
# 프로젝트 루트에서
.\scripts\run_via_cmd.ps1 -original 'aa - ' -folder '.' -RenameDirs
```

테스트:
- 이 저장소는 pytest 기반 테스트가 포함되어 있으며, venv에서 아래처럼 실행하세요:
```powershell
# 가상환경 활성화
. .\.venv\Scripts\Activate.ps1
pytest -q
```
