package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

public final class CommandDraftHandoffTest {
    @Test public void preservesWholeTypedOrVoiceDraftWithoutParsingTools() {
        String draft="  Please open calculator after reviewing this request 😀  ";
        assertSame(draft,CommandDraftHandoff.validatedDraft(draft));
        assertEquals(draft,CommandDraftHandoff.initialDraft(draft,null,false));
    }

    @Test public void rejectsEmptyAndUnicodeBlankInput() {
        for(String text:new String[]{null,""," \t\r\n","\u00a0\u2003"})reject(text);
    }

    @Test public void maximumCountsUtf16AndNeverTruncates() {
        assertEquals(500,CommandDraftHandoff.validatedDraft(repeat("x",500)).length());
        assertEquals(500,CommandDraftHandoff.validatedDraft(repeat("😀",250)).length());
        reject(repeat("x",501));reject(repeat("😀",251));
    }

    @Test public void malformedUnicodeAndHiddenControlsDoNotCrossHandoff() {
        for(String text:new String[]{"a\uD800","a\uDC00","a\uD800b","a\u0000b","a\u0085b"})reject(text);
        assertEquals("one\ntwo\tthree",CommandDraftHandoff.validatedDraft("one\ntwo\tthree"));
    }

    @Test public void recreatedEditsOverrideOriginalIntentIncludingDeliberateEmptyText() {
        assertEquals("Edited request",CommandDraftHandoff.initialDraft("Original request","Edited request",true));
        assertEquals("",CommandDraftHandoff.initialDraft("Original request","",true));
        assertEquals("   ",CommandDraftHandoff.initialDraft("Original request","   ",true));
    }

    @Test public void corruptOrMissingRestorationNeverReplaysOldIntent() {
        for(String restored:new String[]{null,repeat("x",501),"\uD800"})
            assertEquals("",CommandDraftHandoff.initialDraft("Start focus",restored,true));
        assertEquals("new edit",CommandDraftHandoff.initialDraft(repeat("x",501),"new edit",true));
    }

    @Test public void newVisitUsesNewDraftAndAbsentExtraIsDistinctFromRestoration() {
        assertEquals("New request",CommandDraftHandoff.initialDraft("New request","Old edit",false));
        assertNull(CommandDraftHandoff.initialDraft(null,"Old edit",false));
        try{CommandDraftHandoff.initialDraft("", "Old edit",false);fail("Accepted empty new handoff");}
        catch(IllegalArgumentException expected){ }
    }

    private static String repeat(String text,int count) {
        StringBuilder result=new StringBuilder();for(int i=0;i<count;i++)result.append(text);return result.toString();
    }
    private static void reject(String text) {
        try{CommandDraftHandoff.validatedDraft(text);fail("Accepted invalid handoff");}
        catch(IllegalArgumentException expected){ }
    }
}
