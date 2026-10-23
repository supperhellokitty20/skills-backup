// List functions with no incoming call/jump/flow reference.
// In firmware whose dispatch tables live in RAM, reference queries cannot see
// the table edges, so these "orphans" are the table-reachable handler set
// (parsers, encoders, command handlers) rather than dead code.
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class OrphanFuncs extends GhidraScript {
    @Override
    public void run() throws Exception {
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        int orphans = 0;
        while (it.hasNext()) {
            Function f = it.next();
            Address ep = f.getEntryPoint();
            int codeRefs = 0;
            ReferenceIterator r = currentProgram.getReferenceManager().getReferencesTo(ep);
            while (r.hasNext()) {
                Reference ref = r.next();
                if (ref.getReferenceType().isCall() || ref.getReferenceType().isJump() || ref.getReferenceType().isFlow()) {
                    codeRefs++;
                }
            }
            if (codeRefs == 0) {
                println("ORPHAN " + f.getName() + " @ " + ep + " size=0x" + Long.toHexString(f.getBody().getNumAddresses()));
                orphans++;
            }
        }
        println("### ORPHANS " + orphans);
    }
}
