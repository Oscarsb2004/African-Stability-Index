// Wonders (P61): the absolute highlights of the continent, natural and human-made, each with a few photographs.
// The section is planned; nothing here invents content before its sources' terms are read.

export default function WondersPanel() {
  return (
    <div className="panel-body">
      <h3>Wonders of Africa</h3>
      <p>
        The continent's absolute highlights: mountains and rift valleys, rainforests, deserts, great rivers and
        falls, reserves and migrations, and the sites people built. Each wonder gets a few photographs. One click
        opens a photo full screen, swiping moves through the set, and one more click closes it.
      </p>
      <ul className="coming">
        <li><b>Which places</b><span className="muted small">A short list chosen by stated criteria, drawn from
          Wikidata (CC0) and the UNESCO World Heritage List</span></li>
        <li><b>Photographs</b><span className="muted small">Wikimedia Commons, each with its own licence and
          credit; a file without a stated licence is never shown</span></li>
      </ul>
    </div>
  );
}
