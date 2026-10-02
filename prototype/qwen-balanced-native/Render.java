package dev.focuspilot.prototype;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
/** Render only: JNI is loaded by LocalModel static initialization; no model calls. */
public final class Render {
 public static void main(String[] args) throws Exception {
  if(args.length!=3) throw new IllegalArgumentException("requests, prompts, grammar required");
  List<String> output=new ArrayList<>(); Set<String> ids=new HashSet<>();
  for(String row:Files.readAllLines(Path.of(args[0]),StandardCharsets.UTF_8)) {
   String[] f=row.split("\t",-1);
   if(f.length!=2||!f[0].matches("[A-Za-z0-9_-]{1,64}")||!ids.add(f[0])||f[1].isBlank()||f[1].length()>500
       ||f[1].chars().anyMatch(c->c<32||c==127||c==0x2028||c==0x2029)) throw new IllegalArgumentException("Invalid bounded row");
   output.add(f[0]+"\t"+Base64.getEncoder().encodeToString(LocalModel.renderPrompt(f[1]).getBytes(StandardCharsets.UTF_8)));
  }
  if(output.isEmpty()||output.size()>200) throw new IllegalArgumentException("1-200 rows required");
  Files.write(Path.of(args[1]),output,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
  Files.writeString(Path.of(args[2]),LocalModel.INTENT_GRAMMAR,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
 }
}
