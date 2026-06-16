using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using AIChat.Utils;

namespace AIChat.Services
{
    public static class ProcessHelper
    {
        public static void KillProcessTree(Process process)
        {
            if (process == null || process.HasExited) return;

            try
            {
                int pid = process.Id;
                if (IsWindows())
                {
                    Log.Info($"[TTS Cleanup] 使用 taskkill 终止进程树 (PID: {pid})");
                    RunProcess("taskkill", $"/T /F /PID {pid}");
                    Log.Info($"[TTS Cleanup] taskkill 执行完毕 (PID: {pid})");
                    return;
                }

                Log.Info($"[TTS Cleanup] 使用 Unix kill 终止 TTS 进程 (PID: {pid})");
                RunProcess("pkill", $"-TERM -P {pid}");
                RunProcess("kill", $"-TERM {pid}");

                if (!process.WaitForExit(3000) && !process.HasExited)
                {
                    RunProcess("pkill", $"-KILL -P {pid}");
                    RunProcess("kill", $"-KILL {pid}");
                }

                Log.Info($"[TTS Cleanup] Unix kill 执行完毕 (PID: {pid})");
            }
            catch (Exception ex)
            {
                Log.Warning($"[TTS Cleanup] 关闭进程失败: {ex.Message}");
            }
        }

        private static bool IsWindows()
        {
            return Path.DirectorySeparatorChar == '\\';
        }

        private static void RunProcess(string fileName, string arguments)
        {
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = arguments,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using (Process killer = Process.Start(psi))
            {
                killer.WaitForExit(3000);
            }
        }
    }
}
