package dev.focuspilot.qualcomm.research;

/** Exact already-public deployment-config requests. No arbitrary Intent/input command. */
public final class SyntheticCases {
    private SyntheticCases() {}
    private static final String[] CASES = {
        "Start focus", "Pause focus", "Do not start focus",
        "Start focus and set an alarm", "Send a payment to my friend"
    };
    public static int count() { return CASES.length; }
    public static String at(int index) {
        if (index < 0 || index >= CASES.length) throw new IllegalArgumentException("Unknown synthetic case");
        return CASES[index];
    }
    public static String[] labels() { return CASES.clone(); }
}
