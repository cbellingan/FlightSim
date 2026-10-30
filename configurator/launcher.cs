using System;
using System.Diagnostics;
using System.IO;
using System.Net.Sockets;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("X-Plane 12 VR Configurator")]
[assembly: AssemblyDescription("One-Click Standalone Launcher for X-Plane 12 + Meta Quest Pro + OFXR-Bridge VR Configurator")]
[assembly: AssemblyProduct("X-Plane 12 VR Configurator")]
[assembly: AssemblyVersion("1.2.0.0")]

namespace XPlaneVRConfigurator
{
    static class Program
    {
        private const int PORT = 8765;
        private const string URL = "http://127.0.0.1:8765";
        private const string FALLBACK_APP_DIR = @"C:\Users\cb\.gemini\antigravity\scratch\xplane-quest3-configurator";

        [STAThread]
        static void Main(string[] args)
        {
            bool openBrowser = true;
            foreach (string a in args)
            {
                if (string.Equals(a, "--no-browser", StringComparison.OrdinalIgnoreCase))
                {
                    openBrowser = false;
                }
            }

            try
            {
                string appDir = ResolveAppDir();
                string scriptPath = Path.Combine(appDir, "configurator.py");
                if (!File.Exists(scriptPath))
                {
                    MessageBox.Show(
                        "Could not find configurator.py at:\n" + scriptPath,
                        "X-Plane 12 VR Configurator",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                // Ensure OFXRBridgeTray.exe is running in user session if present
                EnsureOfxrTrayRunning(appDir);

                if (!IsPortOpen(PORT, 250))
                {
                    string pythonExe = ResolvePythonExe();
                    if (string.IsNullOrEmpty(pythonExe))
                    {
                        MessageBox.Show(
                            "Could not find a Python 3 installation to start the configurator server.",
                            "X-Plane 12 VR Configurator",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error
                        );
                        return;
                    }

                    ProcessStartInfo psi = new ProcessStartInfo
                    {
                        FileName = pythonExe,
                        Arguments = "\"" + scriptPath + "\" --no-browser",
                        WorkingDirectory = appDir,
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        WindowStyle = ProcessWindowStyle.Hidden
                    };
                    Process.Start(psi);

                    // Wait up to 4.5 seconds for the HTTP server to accept connections
                    for (int i = 0; i < 45; i++)
                    {
                        if (IsPortOpen(PORT, 150))
                        {
                            break;
                        }
                        Thread.Sleep(100);
                    }
                }

                if (openBrowser)
                {
                    Process.Start(new ProcessStartInfo(URL) { UseShellExecute = true });
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Failed to launch X-Plane 12 VR Configurator:\n\n" + ex.Message,
                    "X-Plane 12 VR Configurator",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

        private static string ResolveAppDir()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
            if (File.Exists(Path.Combine(baseDir, "configurator.py")))
            {
                return baseDir;
            }
            return FALLBACK_APP_DIR;
        }

        private static string ResolvePythonExe()
        {
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string winAppsDir = Path.Combine(localAppData, "Microsoft", "WindowsApps");

            if (Directory.Exists(winAppsDir))
            {
                try
                {
                    string[] pkgDirs = Directory.GetDirectories(winAppsDir, "PythonSoftwareFoundation.Python*");
                    foreach (string dir in pkgDirs)
                    {
                        string pyw = Path.Combine(dir, "pythonw.exe");
                        if (File.Exists(pyw)) return pyw;
                        string py = Path.Combine(dir, "python.exe");
                        if (File.Exists(py)) return py;
                    }
                }
                catch { }

                string aliasPyw = Path.Combine(winAppsDir, "pythonw.exe");
                if (File.Exists(aliasPyw)) return aliasPyw;
                string aliasPy = Path.Combine(winAppsDir, "python.exe");
                if (File.Exists(aliasPy)) return aliasPy;
            }

            string[] candidates = new string[]
            {
                @"C:\Program Files\Python312\pythonw.exe",
                @"C:\Program Files\Python311\pythonw.exe",
                @"C:\Program Files\Python310\pythonw.exe",
                @"C:\Program Files\Python39\pythonw.exe",
                "pythonw.exe",
                "python.exe"
            };

            foreach (string c in candidates)
            {
                if (Path.IsPathRooted(c))
                {
                    if (File.Exists(c)) return c;
                }
                else
                {
                    return c;
                }
            }
            return "python.exe";
        }

        private static void EnsureOfxrTrayRunning(string appDir)
        {
            try
            {
                Process[] existing = Process.GetProcessesByName("OFXRBridgeTray");
                if (existing != null && existing.Length > 0)
                {
                    return;
                }

                string trayExe = Path.Combine(appDir, "ofxr-bridge", "OFXR-BRIDGE-0.3.1-v681", "OFXRBridgeTray.exe");
                if (File.Exists(trayExe))
                {
                    ProcessStartInfo psi = new ProcessStartInfo
                    {
                        FileName = trayExe,
                        WorkingDirectory = Path.GetDirectoryName(trayExe),
                        UseShellExecute = false,
                        CreateNoWindow = true
                    };
                    Process.Start(psi);
                }
            }
            catch { }
        }

        private static bool IsPortOpen(int port, int timeoutMs)
        {
            try
            {
                using (TcpClient client = new TcpClient())
                {
                    IAsyncResult result = client.BeginConnect("127.0.0.1", port, null, null);
                    bool success = result.AsyncWaitHandle.WaitOne(TimeSpan.FromMilliseconds(timeoutMs));
                    if (!success)
                    {
                        return false;
                    }
                    client.EndConnect(result);
                    return true;
                }
            }
            catch
            {
                return false;
            }
        }
    }
}
