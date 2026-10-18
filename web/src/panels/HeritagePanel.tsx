// Heritage (name pending, plan ruling 7.6): the section is planned; nothing here invents content before its
// sources' terms are read.

export default function HeritagePanel() {
  return (
    <div className="panel-body">
      <h3>Africa's landscapes and heritage</h3>
      <p>
        Mountains, rainforests, reserves and historic sites will appear here, each with a few photographs. One
        click opens a photo full screen, swiping moves through the set, and one more click closes it.
      </p>
      <ul className="coming">
        <li><b>Places</b><span className="muted small">Wikidata (CC0) and the UNESCO World Heritage List</span></li>
        <li><b>Photographs</b><span className="muted small">Wikimedia Commons, each with its own licence and
          credit; a file without a stated licence is never shown</span></li>
      </ul>
    </div>
  );
}
