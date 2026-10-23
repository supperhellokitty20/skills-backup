// Print all references TO the given address(es), with the referencing function.
// Use on a flash literal-pool address to recover the functions that read a
// RAM pointer cell the disassembler cannot resolve.
// Args: <addr> [<addr> ...]
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class Xrefs extends GhidraScript {
    @Override
    public void run() throws Exception {
        for (String a : getScriptArgs()) {
            Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(a);
            println("### XREFS TO " + addr);
            ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(addr);
            int n = 0;
            while (it.hasNext()) {
                Reference r = it.next();
                Address from = r.getFromAddress();
                Function f = getFunctionContaining(from);
                String fn = (f == null) ? "(none)" : (f.getName() + "@" + f.getEntryPoint());
                println(String.format("  from=%s type=%s in=%s", from, r.getReferenceType(), fn));
                n++;
            }
            println("### total=" + n);
        }
    }
}
