package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Seen development cases; actual JNI proposals only, no tools or phone actions. */
public final class DevBaseline {
    public static void main(String[] args) throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("Selected model and TSV required");
        Path input=Path.of(args[1]);
        if(!Files.isRegularFile(input)||Files.size(input)>8*1024*1024)throw new IllegalArgumentException("Invalid selected input");
        var rows=Files.readAllLines(input,StandardCharsets.UTF_8);var ids=new HashSet<String>();
        if(rows.isEmpty()||rows.size()>4096)throw new IllegalArgumentException("Invalid row count");
        for(String row:rows){
            String[] fields=row.split("\t",-1);
            if(fields.length!=2||!fields[0].matches("[A-Za-z0-9_-]{1,64}")||!ids.add(fields[0])||fields[1].isBlank()||fields[1].length()>500||fields[1].chars().anyMatch(c->c<32||c==127||c==0x2028||c==0x2029))throw new IllegalArgumentException("Invalid development input");
        }
        long begin=System.nanoTime();
        try(LocalModel model=new LocalModel(args[0])){
            System.out.println("LOAD\t"+(System.nanoTime()-begin));
            for(String row:rows){String[] fields=row.split("\t",-1);begin=System.nanoTime();String result=model.generateIntent(fields[1],false);
                System.out.println(fields[0]+"\t"+(System.nanoTime()-begin)+"\t"+Base64.getEncoder().encodeToString(result.getBytes(StandardCharsets.UTF_8)));System.out.flush();}
        }
    }
}
