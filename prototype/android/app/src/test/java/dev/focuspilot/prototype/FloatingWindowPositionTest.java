package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

public class FloatingWindowPositionTest {
    private static void position(int x, int y, FloatingWindowPosition.Position actual) {
        assertEquals(x, actual.x);
        assertEquals(y, actual.y);
    }

    @Test public void ordinaryPositionsKeepWholeWindowInUsableRegion() {
        position(43, 71, FloatingWindowPosition.clamp(43, 71, 120, 90, 400, 600));
        position(0, 0, FloatingWindowPosition.clamp(-1, -500, 120, 90, 400, 600));
        position(280, 510, FloatingWindowPosition.clamp(999, 999, 120, 90, 400, 600));
        position(280, 510, FloatingWindowPosition.clamp(280, 510, 120, 90, 400, 600));
    }

    @Test public void oversizedOrEqualWindowAnchorsOnlyAffectedAxis() {
        position(0, 73, FloatingWindowPosition.clamp(80, 73, 401, 90, 400, 600));
        position(80, 0, FloatingWindowPosition.clamp(80, 73, 120, 601, 400, 600));
        position(0, 0, FloatingWindowPosition.clamp(80, 73, 400, 600, 400, 600));
    }

    @Test public void invalidGeometryHasDeterministicOriginOnAffectedAxis() {
        for (int invalid : new int[]{0, -1, Integer.MIN_VALUE}) {
            position(0, 73, FloatingWindowPosition.clamp(80, 73, invalid, 90, 400, 600));
            position(80, 0, FloatingWindowPosition.clamp(80, 73, 120, invalid, 400, 600));
            position(0, 73, FloatingWindowPosition.clamp(80, 73, 120, 90, invalid, 600));
            position(80, 0, FloatingWindowPosition.clamp(80, 73, 120, 90, 400, invalid));
        }
    }

    @Test public void extremeCoordinatesAndSizesNeverWrapAround() {
        position(Integer.MAX_VALUE-1, 0, FloatingWindowPosition.clamp(
                Integer.MAX_VALUE, Integer.MIN_VALUE, 1, 1, Integer.MAX_VALUE, Integer.MAX_VALUE));
        position(0, 0, FloatingWindowPosition.clamp(Integer.MIN_VALUE, Integer.MAX_VALUE,
                Integer.MAX_VALUE, Integer.MAX_VALUE, 1, 1));
    }

    @Test public void dragUsesOriginalDownPositionWithoutAccumulatingMoves() {
        position(110, 130, FloatingWindowPosition.drag(100, 100, 10, 30, 20, 20, 300, 300));
        position(120, 140, FloatingWindowPosition.drag(100, 100, 20, 40, 20, 20, 300, 300));
        position(120, 140, FloatingWindowPosition.drag(100, 100, 20, 40, 20, 20, 300, 300));
        position(90, 80, FloatingWindowPosition.drag(100, 100, -10, -20, 20, 20, 300, 300));
    }

    @Test public void dragCanReturnFromClampedEdgeUsingOriginalDownPosition() {
        position(280, 0, FloatingWindowPosition.drag(100, 100, 1000, -1000, 20, 20, 300, 300));
        position(105, 105, FloatingWindowPosition.drag(100, 100, 5, 5, 20, 20, 300, 300));
    }

    @Test public void dragAdditionDoesNotOverflowIntegerRange() {
        position(280, 0, FloatingWindowPosition.drag(Integer.MAX_VALUE, Integer.MIN_VALUE,
                Integer.MAX_VALUE, Integer.MIN_VALUE, 20, 20, 300, 300));
        position(0, 0, FloatingWindowPosition.drag(Integer.MIN_VALUE, Integer.MAX_VALUE,
                Integer.MAX_VALUE, Integer.MIN_VALUE, 20, 20, 300, 300));
    }

    @Test public void clampIsIdempotentAndBoundsHoldAcrossSizeExtremes() {
        int[] coordinates = {Integer.MIN_VALUE, -20, 0, 5, 200, Integer.MAX_VALUE};
        int[] windows = {Integer.MIN_VALUE, -1, 0, 1, 20, Integer.MAX_VALUE};
        int[] available = {Integer.MIN_VALUE, -1, 0, 1, 100, Integer.MAX_VALUE};
        for (int coordinate : coordinates) for (int window : windows) for (int size : available) {
            FloatingWindowPosition.Position p = FloatingWindowPosition.clamp(coordinate, coordinate, window, window, size, size);
            int maximum = window <= 0 || size <= 0 || window >= size ? 0 : size-window;
            assertTrue(p.x >= 0 && p.x <= maximum);
            position(p.x, p.y, FloatingWindowPosition.clamp(p.x, p.y, window, window, size, size));
        }
    }
}
