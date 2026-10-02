package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

/** Host-only real JNI research; no phone API, persistence, tool or external action. */
public final class TaskDraftEval {
    private static String encode(String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }
    private static String decode(String value) {
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }
    public static void main(String[] args) throws Exception {
        if (args.length == 2 && args[0].equals("inventory")) {
            System.out.println("GRAMMAR\t" + encode(TaskDraft.GRAMMAR));
            for (String line : Files.readAllLines(Path.of(args[1]))) {
                String[] fields = line.split("\t", 2);
                System.out.println(fields[0] + "\t" + encode(TaskDraft.renderPrompt(decode(fields[1]))));
            }
            return;
        }
        if (args.length == 2 && args[0].equals("validate")) {
            for (String line : Files.readAllLines(Path.of(args[1]))) {
                String[] fields = line.split("\t", 2);
                try {
                    String text = decode(fields[1]);
                    if (text.matches("\\s*\\{\\s*\"steps\"\\s*:\\s*\\[\\s*\\]\\s*\\}\\s*")) {
                        System.out.println(fields[0] + "\tDECLINE");
                        continue;
                    }
                    TaskPlan plan = TaskDraft.parseOutput(text);
                    System.out.println(fields[0] + "\tPLAN_" + plan.stepCount());
                } catch (IllegalArgumentException error) {
                    System.out.println(fields[0] + "\tINVALID");
                }
            }
            return;
        }
        if (args.length != 3 || !args[0].equals("capture"))
            throw new IllegalArgumentException("inventory/validate input.tsv OR capture model.gguf input.tsv");
        long loadStarted = System.nanoTime();
        long handle = LocalModel.nativeInit(args[1], 1024, 4);
        System.out.println("LOAD\t" + (System.nanoTime() - loadStarted));
        System.out.flush();
        Object stateLock = new Object();
        int[] activeToken = {0};
        ScheduledExecutorService watchdog = Executors.newSingleThreadScheduledExecutor();
        try {
            int token = 0;
            for (String line : Files.readAllLines(Path.of(args[2]))) {
                String[] fields = line.split("\t", 2);
                String prompt = TaskDraft.renderPrompt(decode(fields[1]));
                final int request = ++token;
                synchronized (stateLock) {
                    LocalModel.nativePrepare(handle);
                    activeToken[0] = request;
                }
                ScheduledFuture<?> deadline = watchdog.schedule(() -> {
                    synchronized (stateLock) {
                        if (activeToken[0] == request) {
                            LocalModel.nativeCancel(handle);
                            activeToken[0] = -request;
                        }
                    }
                }, 20, TimeUnit.SECONDS);
                long start = System.nanoTime();
                try {
                    String result = LocalModel.nativeGenerate(handle, prompt, TaskDraft.GRAMMAR, 128, false);
                    System.out.println(fields[0] + "\t" + (System.nanoTime() - start) + "\tOK\t" + encode(result));
                } catch (IllegalStateException error) {
                    System.out.println(fields[0] + "\t" + (System.nanoTime() - start) + "\tERROR\t" + encode(error.getMessage()));
                } finally {
                    deadline.cancel(false);
                    synchronized (stateLock) { activeToken[0] = 0; }
                }
                System.out.flush();
            }
        } finally {
            watchdog.shutdownNow();
            LocalModel.nativeClose(handle);
        }
    }
}
