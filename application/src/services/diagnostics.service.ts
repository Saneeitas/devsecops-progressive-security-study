import { exec } from "node:child_process";
import { promisify } from "node:util";

const execAsync = promisify(exec);

export type ResearchDiagnosticTarget = "localhost" | "localhost;printf V02_CANARY";

export async function runResearchDiagnostic(target: ResearchDiagnosticTarget) {
  // V02: controlled command-injection sink. The controller permits only the local
  // value and one harmless canary payload; no external or destructive input is accepted.
  const { stdout } = await execAsync(`printf 'diagnostic:'; printf ${target}`, {
    timeout: 1000,
    maxBuffer: 1024
  });
  return { target, output: stdout };
}
