package dev.focuspilot.prototype;

/** Coordinates relative to the usable region for a TOP|LEFT floating window. */
public final class FloatingWindowPosition {
    private FloatingWindowPosition() {}

    public static final class Position {
        public final int x;
        public final int y;

        private Position(int x, int y) {
            this.x = x;
            this.y = y;
        }
    }

    /**
     * Keeps a fitting window inside the caller's usable region. Invalid geometry
     * and windows too large to fit anchor the affected axis at zero; callers may
     * resize an oversized window separately. Insets are already excluded by the
     * caller, so these coordinates do not contain an additional inset offset.
     */
    public static Position clamp(int x, int y, int windowWidth, int windowHeight,
                                 int availableWidth, int availableHeight) {
        return clampCoordinates(x, y, windowWidth, windowHeight, availableWidth, availableHeight);
    }

    /**
     * deltaX/deltaY are the CURRENT total displacement from pointer-down, not
     * displacement since the previous move. Always pass the original downX/Y.
     * Long intermediates prevent integer wraparound before clamping.
     */
    public static Position drag(int downX, int downY, int deltaX, int deltaY,
                                int windowWidth, int windowHeight,
                                int availableWidth, int availableHeight) {
        return clampCoordinates((long) downX + deltaX, (long) downY + deltaY,
                windowWidth, windowHeight, availableWidth, availableHeight);
    }

    private static Position clampCoordinates(long x, long y, int windowWidth, int windowHeight,
                                             int availableWidth, int availableHeight) {
        return new Position(clampAxis(x, windowWidth, availableWidth),
                clampAxis(y, windowHeight, availableHeight));
    }

    private static int clampAxis(long coordinate, int windowSize, int availableSize) {
        if (windowSize <= 0 || availableSize <= 0 || windowSize >= availableSize) return 0;
        long maximum = (long) availableSize - windowSize;
        return (int) Math.max(0L, Math.min(coordinate, maximum));
    }
}
