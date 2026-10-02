package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Locale;

/** Immutable live-label context. Stores a goal hash, never the original goal. */
public final class LivePreferenceScope {
    public static final int SCHEMA=1;
    public final int schema=SCHEMA;
    public final String mappingVersion=ObservationSnapshot.MAPPING_VERSION;
    public final String selectedPackage,goalSHA256;
    public final long budgetMs,continuousLimitMs,plannedFocusMs;
    private final String fingerprint;
    /** Restoration uses only the stored hash; never pass plaintext to this constructor. */
    public LivePreferenceScope(String selectedPackage,long budgetMs,long continuousLimitMs,long plannedFocusMs,String goalSHA256) {
        if(!MonitorConfig.valid(selectedPackage,budgetMs) || continuousLimitMs<0 || continuousLimitMs>86_400_000 || plannedFocusMs<0 || plannedFocusMs>86_400_000)
            throw new IllegalArgumentException("Invalid preference scope settings");
        if(goalSHA256==null || !goalSHA256.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("A lowercase SHA256 goal hash is required");
        this.selectedPackage=selectedPackage;this.budgetMs=budgetMs;this.continuousLimitMs=continuousLimitMs;this.plannedFocusMs=plannedFocusMs;this.goalSHA256=goalSHA256;
        fingerprint=sha256("schema="+schema+"\nmapping="+mappingVersion+"\npackage="+selectedPackage+"\nbudget="+budgetMs+
            "\ncontinuous="+continuousLimitMs+"\nplanned="+plannedFocusMs+"\ngoal="+goalSHA256+"\n");
    }
    public static LivePreferenceScope fromGoal(String selectedPackage,long budgetMs,long continuousLimitMs,long plannedFocusMs,String goal) {
        if(goal==null || goal.length()>500) throw new IllegalArgumentException("Goal must be present and at most 500 characters");
        return new LivePreferenceScope(selectedPackage,budgetMs,continuousLimitMs,plannedFocusMs,sha256(goal));
    }
    public String fingerprint() { return fingerprint; }
    public boolean matches(ObservationSnapshot snapshot) {
        return snapshot!=null && selectedPackage.equals(snapshot.selectedPackage) &&
            mappingVersion.equals(ObservationSnapshot.MAPPING_VERSION) && budgetMs==snapshot.budgetMs &&
            continuousLimitMs==snapshot.continuousLimitMs && plannedFocusMs==snapshot.plannedFocusMs;
    }
    @Override public boolean equals(Object other) { return other instanceof LivePreferenceScope && fingerprint.equals(((LivePreferenceScope)other).fingerprint); }
    @Override public int hashCode() { return fingerprint.hashCode(); }
    private static String sha256(String value) {
        try {
            byte[] digest=MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
            StringBuilder result=new StringBuilder();for(byte part:digest)result.append(String.format(Locale.US,"%02x",part&255));return result.toString();
        } catch(NoSuchAlgorithmException impossible) { throw new IllegalStateException("SHA256 unavailable",impossible); }
    }
}
