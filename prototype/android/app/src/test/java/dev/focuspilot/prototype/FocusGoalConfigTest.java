package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

public class FocusGoalConfigTest {
    @Test public void optionalLimitsRemainUnknown() {
        FocusGoalConfig value=FocusGoalConfig.parse("  Finish outline  ","","0");
        assertEquals("Finish outline",value.goal);assertEquals(0,value.plannedMs);assertEquals(0,value.continuousMs);
    }
    @Test public void exactDeclaredLimitsAndBoundary() {
        FocusGoalConfig value=FocusGoalConfig.parse("Outline","25","1440");
        assertEquals(1_500_000,value.plannedMs);assertEquals(86_400_000,value.continuousMs);
    }
    @Test public void ambiguousAndOutOfRangeDurationsRejected() {
        for(String value:new String[]{"1.5","-1","25 minutes","1441","9999999999","00"}) {
            assertThrows(IllegalArgumentException.class,()->FocusGoalConfig.parse("Outline",value,""));
        }
    }
    @Test public void PrivateGoalBoundedAndSingleLine() {
        assertThrows(IllegalArgumentException.class,()->FocusGoalConfig.parse("x".repeat(121),"",""));
        assertThrows(IllegalArgumentException.class,()->FocusGoalConfig.parse("task\nother","",""));
    }
}
