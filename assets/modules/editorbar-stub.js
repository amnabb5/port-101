/* Local stub replacing the remote Framer editor-bar loader.
 * The Framer editor bar is an account-bound editing UI and is not part of
 * the cloned site. This stub keeps the runtime's import path functional
 * (offline) while rendering nothing. */
export function createEditorBar() {
  const FramerEditorBarStub = () => null;
  return FramerEditorBarStub;
}
export default createEditorBar;
