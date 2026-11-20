package scratch.patch_test;

import org.python.objectweb.asm.*;
import java.io.*;

public class Patcher {
    public static void main(String[] args) throws Exception {
        File inputFile = new File("com/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl.class");
        FileInputStream fis = new FileInputStream(inputFile);
        ClassReader cr = new ClassReader(fis);
        fis.close();

        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_MAXS);
        ClassAdapter ca = new ClassAdapter(cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String desc, String signature, String[] exceptions) {
                if (name.equals("add") && desc.equals("(Lcom/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl;)Z")) {
                    System.out.println("Patching method: " + name + desc);
                    final MethodVisitor originalMv = super.visitMethod(access, name, desc, signature, exceptions);
                    return new MethodAdapter(originalMv) {
                        @Override
                        public void visitCode() {
                            originalMv.visitCode();
                            originalMv.visitVarInsn(Opcodes.ALOAD, 0);
                            originalMv.visitVarInsn(Opcodes.ALOAD, 1);
                            originalMv.visitMethodInsn(
                                Opcodes.INVOKESTATIC,
                                "com/sun/electric/database/geometry/PolyTreeHelper",
                                "add",
                                "(Lcom/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl;Lcom/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl;)Z"
                            );
                            originalMv.visitInsn(Opcodes.IRETURN);
                            originalMv.visitMaxs(2, 2);
                            originalMv.visitEnd();
                        }

                        // Ignore all original method instructions
                        @Override public void visitFrame(int type, int nLocal, Object[] local, int nStack, Object[] stack) {}
                        @Override public void visitInsn(int opcode) {}
                        @Override public void visitIntInsn(int opcode, int operand) {}
                        @Override public void visitVarInsn(int opcode, int var) {}
                        @Override public void visitTypeInsn(int opcode, String type) {}
                        @Override public void visitFieldInsn(int opcode, String owner, String name, String desc) {}
                        @Override public void visitMethodInsn(int opcode, String owner, String name, String desc) {}
                        @Override public void visitJumpInsn(int opcode, Label label) {}
                        @Override public void visitLabel(Label label) {}
                        @Override public void visitLdcInsn(Object cst) {}
                        @Override public void visitIincInsn(int var, int increment) {}
                        @Override public void visitTableSwitchInsn(int min, int max, Label dflt, Label[] labels) {}
                        @Override public void visitLookupSwitchInsn(Label dflt, int[] keys, Label[] labels) {}
                        @Override public void visitMultiANewArrayInsn(String desc, int dims) {}
                        @Override public void visitTryCatchBlock(Label start, Label end, Label handler, String type) {}
                        @Override public void visitLocalVariable(String name, String desc, String signature, Label start, Label end, int index) {}
                        @Override public void visitLineNumber(int line, Label start) {}
                        @Override public void visitMaxs(int maxStack, int maxLocals) {}
                        @Override public void visitEnd() {}
                    };
                }
                return super.visitMethod(access, name, desc, signature, exceptions);
            }
        };

        cr.accept(ca, 0);
        byte[] patchedBytes = cw.toByteArray();

        FileOutputStream fos = new FileOutputStream(inputFile);
        fos.write(patchedBytes);
        fos.close();
        System.out.println("Successfully patched " + inputFile.getPath() + " (" + patchedBytes.length + " bytes)");
    }
}
