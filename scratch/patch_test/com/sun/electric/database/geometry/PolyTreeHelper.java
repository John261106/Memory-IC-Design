package com.sun.electric.database.geometry;

import java.awt.geom.Point2D;
import java.awt.geom.Rectangle2D;

public class PolyTreeHelper {
    public static boolean isChildHole(PolyBase parent, PolyBase child) {
        if (parent == null || child == null) return false;
        Rectangle2D rParent = parent.getBounds2D();
        Rectangle2D rChild = child.getBounds2D();
        if (rParent == null || rChild == null) return false;
        
        // Strict Bounding-Box Interior Check:
        // A polygon is only recognized as a child hole if its bounding box is strictly
        // within the interior limits of the parent polygon.
        // If the shape touches along the outer perimeter (e.g. boundary edge overlap),
        // it is kept as an independent Root (Level-0) polygon.
        double eps = 1e-4;
        if (rChild.getMinX() <= rParent.getMinX() + eps ||
            rChild.getMaxX() >= rParent.getMaxX() - eps ||
            rChild.getMinY() <= rParent.getMinY() + eps ||
            rChild.getMaxY() >= rParent.getMaxY() - eps) {
            return false;
        }
        
        PolyBase.Point[] pts = child.getPoints();
        if (pts == null || pts.length == 0) return false;
        return parent.contains(pts[0]);
    }

    public static boolean add(PolyBase.PolyBaseTreeImpl self, PolyBase.PolyBaseTreeImpl t) {
        if (!isChildHole(self.poly, t.poly)) {
            return false;
        }
        if (self.sons == null || self.sons.isEmpty()) {
            self.addSonLowLevel(t);
        } else {
            for (PolyBase.PolyBaseTree b : self.sons) {
                PolyBase.PolyBaseTreeImpl bi = (PolyBase.PolyBaseTreeImpl) b;
                if (isChildHole(bi.poly, t.poly)) {
                    return bi.add(t);
                }
            }
            self.sons.add(t);
        }
        return true;
    }
}
