using System;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Terraria.ModLoader;

namespace LonkBirds.Bridge;

/// <summary>Offline-safe, loopback-only Terraria adapter for the XC portal bridge.</summary>
public sealed class LonkBridgeClient : ModSystem
{
    private static readonly object Gate = new();
    private static CancellationTokenSource? cancellation;
    private static Task? worker;
    private static string? lastBuildRequestId;
    private static readonly string[] Queue = new string[16];
    private static int queueCount;

    public override void OnWorldLoad()
    {
        lock (Gate)
        {
            cancellation?.Cancel();
            cancellation = new CancellationTokenSource();
            worker = Task.Run(() => Run(cancellation.Token));
            Enqueue("{\"version\":1,\"kind\":\"hello\",\"world\":\"terraria\",\"payload\":{}}");
            Enqueue("{\"version\":1,\"kind\":\"visit\",\"bird\":\"lonk\",\"world\":\"terraria\",\"payload\":{}}");
        }
    }

    public override void OnWorldUnload()
    {
        lock (Gate)
        {
            cancellation?.Cancel();
            cancellation = null;
            queueCount = 0;
        }
    }

public static void ProposeNest(int x, int y)
    {
        lastBuildRequestId = Guid.NewGuid().ToString("N").Substring(0, 12);
        Enqueue("{\"version\":1,\"kind\":\"build_request\",\"bird\":\"lonk\",\"world\":\"terraria\",\"payload\":{\"action\":\"propose\",\"request_id\":\"" + lastBuildRequestId + "\",\"target\":\"nest\",\"bounds\":{\"x\":" + x + ",\"y\":" + y + ",\"width\":6,\"height\":4}}}");
    }

    public static void ApproveLatestNest()
    {
        if (string.IsNullOrEmpty(lastBuildRequestId)) return;
        Enqueue("{\"version\":1,\"kind\":\"build_request\",\"bird\":\"lonk\",\"world\":\"terraria\",\"payload\":{\"action\":\"approve\",\"request_id\":\"" + lastBuildRequestId + "\",\"target\":\"nest\",\"bounds\":{\"x\":0,\"y\":0,\"width\":1,\"height\":1}}}");
    }
    public static void Observe(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return;
        string safe = text.Trim().Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", " ").Replace("\n", " ");
        if (safe.Length > 240) safe = safe.Substring(0, 240);
        Enqueue("{\"version\":1,\"kind\":\"observe\",\"bird\":\"lonk\",\"world\":\"terraria\",\"payload\":{\"text\":\"" + safe + "\"}}");
    }

    private static void Enqueue(string message)
    {
        lock (Gate)
        {
            if (queueCount == Queue.Length) return;
            Queue[queueCount++] = message;
        }
    }

    private static async Task Run(CancellationToken token)
    {
        try
        {
            using TcpClient client = new();
            await client.ConnectAsync(LonkBridgeProtocol.LoopbackHost, LonkBridgeProtocol.DefaultPort, token);
            using NetworkStream stream = client.GetStream();
            while (!token.IsCancellationRequested)
            {
                string? message = null;
                lock (Gate)
                {
                    if (queueCount > 0)
                    {
                        message = Queue[0];
                        Array.Copy(Queue, 1, Queue, 0, queueCount - 1);
                        queueCount--;
                    }
                }
                if (message is null)
                {
                    await Task.Delay(100, token);
                    continue;
                }
                byte[] data = Encoding.UTF8.GetBytes(message + "\n");
                await stream.WriteAsync(data, token);
                await stream.FlushAsync(token);
            }
        }
        catch (OperationCanceledException) { }
        catch (SocketException) { }
        catch (ObjectDisposedException) { }
    }
}



