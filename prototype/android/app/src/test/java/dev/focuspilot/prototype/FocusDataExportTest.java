package dev.focuspilot.prototype;

import org.junit.Test;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import static org.junit.Assert.*;

public class FocusDataExportTest {
    private static final String HASH = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
    private FocusDataExport.Settings settings(String app) {
        return new FocusDataExport.Settings(app, 60_000, 60_000, 60_000, HASH, true, false);
    }
    private FocusDataExport.Record record(long id, FocusDataExport.Settings scope, double[] values) {
        return new FocusDataExport.Record(id, scope, values, FocusDataExport.Label.ALLOW, 1000, 500, 600, "REAL_OBSERVATION");
    }
    private FocusDataExport.Snapshot snapshot(List<FocusDataExport.Record> records) {
        return new FocusDataExport.Snapshot(2000, settings("dev.selected.app"), 95, 1000, false, records);
    }
    private void invalid(Runnable action) {
        try { action.run(); fail("Invalid export was accepted"); } catch (IllegalArgumentException expected) {}
    }
    @Test public void emptyExportHasExplicitPrivacySemanticsAndNoRawGoalField() {
        String json = new String(FocusDataExport.render(snapshot(Collections.emptyList())), StandardCharsets.UTF_8);
        assertTrue(json.endsWith("}\n"));
        assertTrue(json.contains("\"schema\":1"));
        assertTrue(json.contains("\"selected_package\":\"dev.selected.app\""));
        assertTrue(json.contains("\"goal_sha256\":\"" + HASH + "\""));
        assertTrue(json.contains("\"money_moved\":false"));
        assertTrue(json.contains("\"records\":[]"));
        for (String forbidden : new String[]{"\"goal\":", "\"events\":", "\"ui_text\":", "\"api_key\":", "\"screen\":", "\"tensor\":", "\"weights\":"}) assertFalse(json.contains(forbidden));
    }
    @Test public void rawGoalCannotBePassedAsHashOrInjectedViaPackage() {
        invalid(() -> new FocusDataExport.Settings("dev.selected.app",60000,0,0,"Write my secret report",false,false));
        invalid(() -> settings("dev.selected.app\",\"api_key\":\"secret"));
        invalid(() -> settings("dev.selected.\napp"));
    }
    @Test public void otherAppIdentityCannotLeakThroughRecordContext() {
        FocusDataExport.Record other = record(1,settings("org.private.other"),new double[6]);
        invalid(() -> snapshot(Collections.singletonList(other)));
    }
    @Test public void quotesControlsAndUnicodeHaveValidJsonEscapes() {
        assertEquals("\"a\\\"\\\\\\n\\r\\t\\b\\f\\u0000\\u001f\\u00e9\\ud83d\\ude42\"",
                FocusDataExport.quote("a\"\\\n\r\t\b\f\u0000\u001fé🙂"));
        invalid(() -> FocusDataExport.quote("\ud800"));
        invalid(() -> FocusDataExport.quote("\udc00"));
    }
    @Test public void rejectsNonfiniteOutOfRangeAndWrongLengthVectors() {
        for(double bad : new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,-0.01,1.01}) {
            double[] values = new double[6]; values[3]=bad;
            invalid(() -> record(1,settings("dev.selected.app"),values));
        }
        invalid(() -> record(1,settings("dev.selected.app"),new double[5]));
        invalid(() -> record(1,settings("dev.selected.app"),null));
    }
    @Test public void accepts32RecordsButRejects33WithoutTruncation() {
        List<FocusDataExport.Record> records=new ArrayList<>();
        for(int id=1;id<=32;id++) records.add(record(id,settings("dev.selected.app"),new double[]{0,1,.5,.25,.75,.125}));
        byte[] bytes=FocusDataExport.render(snapshot(records));
        assertTrue(bytes.length<=80_000);
        assertTrue(new String(bytes,StandardCharsets.UTF_8).contains("\"id\":32,"));
        records.add(record(33,settings("dev.selected.app"),new double[6]));
        invalid(() -> snapshot(records));
    }
    @Test public void vectorsAndListAreDefensivelyCopied() {
        double[] values=new double[6];
        FocusDataExport.Record record=record(1,settings("dev.selected.app"),values);
        List<FocusDataExport.Record> records=new ArrayList<>(Collections.singletonList(record));
        FocusDataExport.Snapshot snapshot=snapshot(records);
        byte[] before=FocusDataExport.render(snapshot);
        values[0]=Double.NaN;record.features()[1]=Double.NaN;records.clear();
        assertArrayEquals(before,FocusDataExport.render(snapshot));
        try { snapshot.records().clear(); fail("Snapshot mutated"); } catch(UnsupportedOperationException expected) {}
    }
    @Test public void rejectsDuplicateNullAndInvalidRecordIdentity() {
        FocusDataExport.Record record=record(1,settings("dev.selected.app"),new double[6]);
        invalid(() -> snapshot(Arrays.asList(record,record)));
        invalid(() -> snapshot(Collections.singletonList(null)));
        invalid(() -> record(0,settings("dev.selected.app"),new double[6]));
        invalid(() -> record(Long.MAX_VALUE,settings("dev.selected.app"),new double[6]));
    }
    @Test public void onlyRealProvenanceAndCompleteLiveLimitsAreAccepted() {
        invalid(() -> new FocusDataExport.Record(1,settings("dev.selected.app"),new double[6],FocusDataExport.Label.ALLOW,1000,0,0,"SYNTHETIC"));
        invalid(() -> record(1,new FocusDataExport.Settings("dev.selected.app",60000,0,0,HASH,true,false),new double[6]));
    }
    @Test public void invalidOrFutureTimestampsAndOldLabelDelayAreRejected() {
        invalid(() -> new FocusDataExport.Record(1,settings("dev.selected.app"),new double[6],FocusDataExport.Label.NUDGE,0,0,0,"REAL_OBSERVATION"));
        invalid(() -> new FocusDataExport.Record(1,settings("dev.selected.app"),new double[6],FocusDataExport.Label.NUDGE,1000,100,99,"REAL_OBSERVATION"));
        invalid(() -> new FocusDataExport.Record(1,settings("dev.selected.app"),new double[6],FocusDataExport.Label.NUDGE,1000,100,15101,"REAL_OBSERVATION"));
        invalid(() -> new FocusDataExport.Snapshot(999,settings("dev.selected.app"),100,0,false,Collections.singletonList(record(1,settings("dev.selected.app"),new double[6]))));
    }
    @Test public void strictSettingsBalanceAndDurationBoundsAreEnforced() {
        invalid(() -> new FocusDataExport.Settings("dev.selected.app",59999,0,0,HASH,false,false));
        invalid(() -> new FocusDataExport.Settings("dev.selected.app",60000,86400001,0,HASH,false,false));
        invalid(() -> new FocusDataExport.Snapshot(1000,settings("dev.selected.app"),101,0,false,Collections.emptyList()));
        invalid(() -> new FocusDataExport.Snapshot(1000,settings("dev.selected.app"),100,-1,false,Collections.emptyList()));
        invalid(() -> FocusDataExport.render(null));
    }
    @Test public void recordPreservesOwnSettingsContextWithoutAnotherPackageField() {
        FocusDataExport.Settings previous=new FocusDataExport.Settings("dev.selected.app",120000,180000,240000,HASH,false,true);
        String json=new String(FocusDataExport.render(snapshot(Collections.singletonList(record(1,previous,new double[6])))),StandardCharsets.UTF_8);
        assertTrue(json.contains("\"budget_ms\":120000"));
        assertEquals(1,json.split("selected_package",-1).length-1);
        assertTrue(json.contains("\"provenance\":\"REAL_OBSERVATION\""));
        assertTrue(json.contains("\"mapping\":\"selected-events-v1\""));
    }
}
