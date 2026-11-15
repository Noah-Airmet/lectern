// The home page's wall (scripts/wall.ts): books from the library drifting in columns.
// WALL: scans whose first page is a good cover (a cloth or printed binding, no library barcode,
// no modern publisher's cover), chosen by eye from contact sheets of every book's first page.
// Each is a small copy in public/wall/, made by scripts/make_wall.sh; to change the wall, edit
// this list and run the script. Few of the books have such a cover, so BOUND adds books drawn
// as a binding in their shelf's cloth with the title in gilt, chosen to show what the library
// holds. A book that has left the library drops out at build.
export const WALL: string[] = [
  'caesar:the-civil-wars-2',
  'virgil:eclogues-georgics-aeneid-i-vi-1',
  'pliny:letters-1',
  'augustine:confessions-1',
  'catullus:catullus-tibullus-pervigilium-veneris',
  'polybius:the-histories-1',
  'livy:history-of-rome-5',
  'clarke:new-testament-commentary-6',
  'mcclintock-strong:cyclopaedia-of-biblical-theological-6',
  'seixas:manual-hebrew-grammar',
  'gough:new-testament-quotations',
  'deissmann:light-from-the-ancient-east',
  'josephus:works-5',
  'clarke:holy-bible-commentary-4',
  'brown:hebrew-english-lexicon-ot',
  'egt:matthew-to-john-1',
  'burton:harmony-of-the-synoptic-gospels',
  'toy:quotations-in-the-new-testament',
  'egt:2-corinthians-to-colossians-3',
  'egt:acts-to-1-corinthians-2',
  'appian:roman-history-civil-wars-4',
  'egt:1-thessalonians-to-james-4',
  'clarke:holy-bible-commentary-3',
  'cadbury:making-of-luke-acts',
  'wettstein:novum-testamentum-graecum-1',
  'jenson:biographical-encyclopedia-1',
  'denny:papalism',
  'rodkinson:tract-sabbath-1',
  'roberts:mormon-doctrine-of-deity',
  'philostratus:life-of-apollonius-of-tyana-2',
];
// Each with a shorter title for its cover where the book's own is long.
export const BOUND: [string, string?][] = [
  ['jod:01'],
  ['jod:06'],
  ['jod:20'],
  ['pratt:key-to-the-science-of-theology'],
  ['pratt:voice-of-warning', 'A Voice of Warning'],
  ['smith:history-of-the-church', 'History of the Church'],
  ['smith:lectures-on-faith'],
  ['widtsoe:joseph-smith-as-scientist'],
  ['widtsoe:rational-theology', 'Rational Theology'],
  ['young:discourses-of-brigham-young'],
  ['jenson:biographical-encyclopedia-1', 'Biographical Encyclopedia'],
  ['morris:prophecies-of-joseph-smith', 'Prophecies of Joseph Smith'],
  ['npnf1:01-confessions-and-letters', 'Confessions and Letters'],
  ['npnf1:02-city-of-god-and-christian-doctrine'],
  ['npnf2:04-select-works-and-letters'],
  ['npnf2:14-seven-ecumenical-councils'],
  ['npnf2:01-church-history', 'Church History'],
  ['lightfoot:apostolic-fathers'],
  ['josephus:works-of-flavius-josephus'],
  ['schaff:creeds-of-christendom-1', 'The Creeds of Christendom'],
];
export const wallFile = (docId: string) => `/wall/${docId.replace(':', '-')}.webp`;
