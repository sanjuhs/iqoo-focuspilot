package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Frozen Android prompt/JNI baseline on synthetic host cases; executes no action. */
public final class CommandBaseline {
    public static void main(String[] args) throws Exception {
        if(args.length!=2) throw new IllegalArgumentException("Selected model and TSV input required");
        Path input=Path.of(args[1]);
        if(!Files.isRegularFile(input) || Files.size(input)>8*1024*1024)
            throw new IllegalArgumentException("Selected TSV must be a regular file at most 8 MiB");
        var rows=Files.readAllLines(input,StandardCharsets.UTF_8);
        if(rows.isEmpty() || rows.size()>4096) throw new IllegalArgumentException("Expected 1 to 4096 cases");
        var ids=new HashSet<String>();
        for(String row:rows) {
            String[] fields=row.split("\t",-1);
            if(fields.length!=2 || !fields[0].matches("[A-Za-z0-9_-]{1,64}") || !ids.add(fields[0]) ||
                fields[1].isBlank() || fields[1].length()>500 || fields[1].chars().anyMatch(c->c<32 || c==127 || c==0x2028 || c==0x2029))
                throw new IllegalArgumentException("Invalid synthetic input; no model request started");
        }
        long start=System.nanoTime();
        try(LocalModel model=new LocalModel(args[0])) {
            System.out.println("LOAD\t"+(System.nanoTime()-start));
            for(String row:rows) {
                String[] fields=row.split("\t",-1); start=System.nanoTime();
                String result=model.generateIntent(fields[1],false);
                System.out.println(fields[0]+"\t"+(System.nanoTime()-start)+"\t"+
                    Base64.getEncoder().encodeToString(result.getBytes(StandardCharsets.UTF_8)));
                System.out.flush();
            }
        }
    }
}
