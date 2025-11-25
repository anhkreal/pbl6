export async function verifyPin(pin?: string): Promise<boolean> {
  // Verify admin PIN locally against value stored in sessionStorage during login.
  try {
      const rawStored = sessionStorage.getItem('adminPin');
      console.debug('[verifyPin] session adminPin raw:', rawStored);
      if (!rawStored) return false;
      const stored = String(rawStored).trim();
      // if no pin provided, assume auto-verify because adminPin exists
      if (pin === undefined || pin === null) {
        console.debug('[verifyPin] no pin provided, auto-verify using stored adminPin');
        return true;
      }
      const input = String(pin).trim();
      console.debug('[verifyPin] comparing input pin:', input, 'to stored:', stored);
      return input === stored;
  } catch (e) {
    return false;
  }
}
