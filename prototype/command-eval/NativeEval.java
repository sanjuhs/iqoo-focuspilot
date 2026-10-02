package dev.focuspilot.prototype;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
/** Only real JNI inference; no phone tools/permissions/activity calls. */
public final class NativeEval {
 public static void main(String[] args) throws Exception {
  if(args.length!=2)throw new IllegalArgumentException("Model GGUF and cases TSV required");
  long t=System.nanoTime();
  try(LocalModel model=new LocalModel(args[0])) {
   System.out.println("LOAD\t"+(System.nanoTime()-t));
   for(String line:Files.readAllLines(Path.of(args[1]))) {
    String[] fields=line.split("\t",2);String command=new String(Base64.getDecoder().decode(fields[1]),StandardCharsets.UTF_8);
    t=System.nanoTime();String result=model.generateIntent(command,false);
    System.out.println(fields[0]+"\t"+(System.nanoTime()-t)+"\t"+Base64.getEncoder().encodeToString(result.getBytes(StandardCharsets.UTF_8)));System.out.flush();
   }
  }
 }
}
