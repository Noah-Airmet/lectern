// The wall on the search page: title pages chosen by eye. Empty until they are chosen
// (a scan's first page is usually a blank board or a library plate). Each is drawn from a small copy in public/wall/, made by scripts/make_wall.sh
// from the snapshot's page images. To change the wall, edit this list and run the script.
// A document that has left the library, or is no longer openly licensed, drops out at build.
export const WALL: string[] = [];
export const wallFile = (docId: string) => `/wall/${docId.replace(':', '-')}.webp`;
