param([Parameter(Mandatory=$true)][string]$Text, [Parameter(Mandatory=$true)][string]$OutputPath)
Add-Type -AssemblyName System.Speech
$bt2Synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $bt2Synthesizer.SelectVoice('Microsoft Zira Desktop')
    $bt2Synthesizer.Rate = 0
    $bt2Synthesizer.SetOutputToWaveFile($OutputPath)
    $bt2Synthesizer.Speak($Text)
    $bt2Synthesizer.SetOutputToNull()
    $bt2Player = New-Object System.Media.SoundPlayer($OutputPath)
    try { $bt2Player.PlaySync() } finally { $bt2Player.Dispose() }
    Write-Output ('Audio update saved and playback requested: ' + $OutputPath)
} finally { $bt2Synthesizer.Dispose() }
