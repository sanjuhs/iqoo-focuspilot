package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Actual existing CPU JNI, fresh native state per request. No tools or phone. */
public final class JsonRunner {
    public static void main(String[] args) throws Exception {
        if(args.length!=3 || !(args[2].equals("baseline") || args[2].equals("candidate")))
            throw new IllegalArgumentException("model, request TSV and baseline/candidate required");
        Path input=Path.of(args[1]);
        if(!Files.isRegularFile(input)||Files.size(input)>65536)throw new IllegalArgumentException("Invalid input");
        var rows=Files.readAllLines(input,StandardCharsets.UTF_8);var ids=new HashSet<String>();
        if(rows.isEmpty()||rows.size()>100)throw new IllegalArgumentException("Invalid row count");
        for(String row:rows){String[] f=row.split("\t",-1);
            if(f.length!=2||!f[0].matches("[A-Za-z0-9_-]{1,64}")||!ids.add(f[0])||f[1].isBlank()||f[1].length()>500||f[1].chars().anyMatch(c->c<32||c==127||c==0x2028||c==0x2029))throw new IllegalArgumentException("Invalid request");}
        boolean candidate=args[2].equals("candidate");long begin=System.nanoTime();
        long handle=LocalModel.nativeInit(args[0],1024,4);
        try {
            System.out.println("LOAD\t"+(System.nanoTime()-begin));
            for(String row:rows){String[] f=row.split("\t",-1);String prompt=candidate?JsonIntentCandidate.renderPrompt(f[1]):LocalModel.renderPrompt(f[1]);
                LocalModel.nativePrepare(handle);begin=System.nanoTime();
                String result=LocalModel.nativeGenerate(handle,prompt,candidate?JsonIntentCandidate.GRAMMAR:LocalModel.INTENT_GRAMMAR,candidate?JsonIntentCandidate.MAX_TOKENS:128,false);
                System.out.println(f[0]+"\t"+(System.nanoTime()-begin)+"\t"+Base64.getEncoder().encodeToString(result.getBytes(StandardCharsets.UTF_8)));System.out.flush();
            }
        } finally { LocalModel.nativeClose(handle); }
    }
}
