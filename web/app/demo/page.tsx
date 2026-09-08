"use client";

import {
  Activity,
  ArrowRightLeft,
  BadgeCheck,
  BarChart3,
  Bell,
  BookOpen,
  BrainCircuit,
  CalendarDays,
  Check,
  ChevronDown,
  CircleDot,
  ClipboardCheck,
  Clock3,
  Crown,
  Crosshair,
  Dumbbell,
  Flag,
  FileText,
  Gavel,
  Gamepad2,
  History,
  IdCard,
  LayoutDashboard,
  MapPin,
  Medal,
  Menu,
  MessageSquare,
  Plus,
  Play,
  RefreshCw,
  Search,
  Send,
  Settings,
  Shield,
  ShieldCheck,
  Sparkles,
  Swords,
  TimerReset,
  Trophy,
  TrendingUp,
  UserPlus,
  Users,
  Video,
  WalletCards,
  Zap,
  X,
} from "lucide-react";
import { useState } from "react";

const nav = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Club", icon: Users },
  { label: "Market", icon: ArrowRightLeft },
  { label: "Competition", icon: Trophy },
  { label: "Integrity", icon: Gavel },
  { label: "Rankings", icon: BarChart3 },
  { label: "Prestige", icon: Medal },
  { label: "Player Cards", icon: IdCard },
  { label: "Performance", icon: BarChart3 },
  { label: "Identity", icon: ShieldCheck },
];

const lineup = [
  { tag: "NIM • Favour", role: "OBJ", status: "Ready", initials: "FV" },
  { tag: "NIM • Sly", role: "SMG", status: "Ready", initials: "SL" },
  { tag: "NIM • Reign", role: "AR", status: "Ready", initials: "RG" },
  { tag: "NIM • Kage", role: "Flex", status: "Late", initials: "KG" },
  { tag: "NIM • Void", role: "Sniper", status: "Ready", initials: "VD" },
];

const schedule = [
  { time: "20:00", title: "Scrim vs Lagos Elite", meta: "Best of 5 · Team room", accent: "match" },
  { time: "21:30", title: "VOD review", meta: "Summit HP rotations", accent: "review" },
  { time: "FRI", title: "NCS Qualifier — Round 3", meta: "19:00 · Check-in at 18:30", accent: "event" },
];

function Brand() {
  return (
    <div className="brand">
      <div className="brandMark"><Crosshair size={20} strokeWidth={2.4} /></div>
      <div><strong>SquadHub</strong><span>Competitive OS</span></div>
    </div>
  );
}

export default function Home() {
  const [active, setActive] = useState("Overview");
  const [menuOpen, setMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteTag, setInviteTag] = useState("");
  const [toast, setToast] = useState("");
  const [offerStatus, setOfferStatus] = useState<Record<string, string>>({});
  const pageDescriptions: Record<string, string> = {
    Overview: "The operating picture for your club, market and competitions.",
    Club: "Run every roster tier with a permanent, auditable player timeline.",
    Market: "Permanent deals, loans, contracts and registration—all in naira.",
    "Player Cards": "Showcase your roster with collectible cards built from verified match data.",
    Competition: "Official MP and BR seasons, fixtures and organizer controls.",
    Integrity: "Keep official records clean and resolve disputes transparently.",
    Rankings: "Separate leaderboards for pro players, ranked grinders, creators and clubs.",
    Prestige: "Trophies, awards and the career record players carry with them.",
    Performance: "Turn verified match data into the next week of improvement.",
    Identity: "Phone-first access, youth safety and verified organization roles.",
  };

  const notify = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2600);
  };

  return (
    <main className="appShell"><div style={{position:"fixed",bottom:0,left:0,right:0,zIndex:1000,background:"#c9ff4a",color:"#111",padding:12,textAlign:"center"}}>Archived CODM demo. All players, results and actions here are examples. <a href="/" style={{textDecoration:"underline"}}>Open saved workspace</a></div>
      <aside className={`sidebar ${menuOpen ? "sidebarOpen" : ""}`}>
        <div className="sidebarTop">
          <Brand />
          <button className="iconButton closeMenu" onClick={() => setMenuOpen(false)} aria-label="Close navigation"><X size={19} /></button>
        </div>

        <div className="teamSwitcher">
          <div className="teamCrest">N¡M</div>
          <div><span>Current squad</span><strong>N¡M Esports</strong></div>
          <ChevronDown size={16} />
        </div>

        <nav aria-label="Primary navigation">
          <span className="navLabel">Workspace</span>
          {nav.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`navItem ${active === label ? "active" : ""}`}
              onClick={() => { setActive(label); setMenuOpen(false); }}
            >
              <Icon size={18} strokeWidth={2} />
              <span>{label}</span>
              {label === "Market" && <small>3</small>}
              {label === "Integrity" && <small>2</small>}
            </button>
          ))}
        </nav>

        <div className="seasonCard">
          <div><span>Season progress</span><strong>West Africa S4</strong></div>
          <div className="progress"><i /></div>
          <p>11 of 16 matchdays</p>
        </div>

        <button className="navItem settings"><Settings size={18} /><span>Settings</span></button>
        <div className="userCard">
          <div className="avatar">FI</div>
          <div><strong>Favour I.</strong><span>Team manager</span></div>
          <CircleDot size={15} className="online" />
        </div>
      </aside>

      {menuOpen && <button className="scrim" onClick={() => setMenuOpen(false)} aria-label="Close menu overlay" />}

      <section className="workspace">
        <header className="topbar">
          <button className="iconButton menuButton" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Menu size={21} /></button>
          <div className="searchBox">
            <Search size={17} />
            <input aria-label="Search" placeholder="Search players, teams, competitions…" />
            <kbd>⌘ K</kbd>
          </div>
          <div className="topActions">
            <div className="notificationWrap">
              <button className="iconButton notificationButton" onClick={() => setNotificationsOpen((value) => !value)} aria-label="Notifications">
                <Bell size={19} /><i />
              </button>
              {notificationsOpen && (
                <div className="notificationPanel">
                  <strong>Notifications</strong>
                  <p><span>Roster update</span>Kage marked himself late for tonight.</p>
                  <p><span>Transfer offer</span>Royal Ravens sent an offer for Reign.</p>
                </div>
              )}
            </div>
            <button className="primaryButton" onClick={() => setInviteOpen(true)}><UserPlus size={17} /> Invite player</button>
          </div>
        </header>

        <div className="content">
          <div className="pageHeading">
            <div>
              <p className="eyebrow">MONDAY · 10 AUGUST</p>
              <h1>{active === "Overview" ? "African CODM, properly organized." : active}</h1>
              <p>{pageDescriptions[active]}</p>
            </div>
            <div className="headingBadges">
              <span><Shield size={15} /> T2 verified</span>
              <span><Activity size={15} /> 82% readiness</span>
            </div>
          </div>

          {active === "Overview" && <Dashboard onAction={notify} />}
          {active === "Club" && <ClubView onInvite={() => setInviteOpen(true)} onAction={notify} />}
          {active === "Market" && <MarketView status={offerStatus} setStatus={setOfferStatus} onAction={notify} />}
          {active === "Player Cards" && <PlayerCardsView onAction={notify} />}
          {active === "Competition" && <CompetitionView onAction={notify} />}
          {active === "Integrity" && <IntegrityView onAction={notify} />}
          {active === "Rankings" && <RankingsView />}
          {active === "Prestige" && <PrestigeView onAction={notify} />}
          {active === "Performance" && <PerformanceView onAction={notify} />}
          {active === "Identity" && <IdentityView onAction={notify} />}
        </div>
      </section>

      {inviteOpen && (
        <div className="modalLayer" role="presentation" onMouseDown={() => setInviteOpen(false)}>
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="invite-title" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modalIcon"><UserPlus size={20} /></div>
            <button className="iconButton modalClose" onClick={() => setInviteOpen(false)} aria-label="Close invite"><X size={18} /></button>
            <p className="panelKicker">ROSTER INVITE</p>
            <h2 id="invite-title">Bring a player into N¡M</h2>
            <p>Invite by SquadHub gamertag. They’ll have 48 hours to accept before the link expires.</p>
            <label>Player gamertag<input autoFocus value={inviteTag} onChange={(event) => setInviteTag(event.target.value)} placeholder="e.g. NIM • Phantom" /></label>
            <label>Squad role<select defaultValue="player"><option value="player">Player</option><option value="analyst">Analyst</option><option value="coach">Coach</option></select></label>
            <button
              className="primaryButton modalSubmit"
              disabled={!inviteTag.trim()}
              onClick={() => { notify(`Invite sent to ${inviteTag.trim()}`); setInviteTag(""); setInviteOpen(false); }}
            ><Send size={16} /> Send roster invite</button>
          </section>
        </div>
      )}

      {toast && <div className="toast" role="status"><Check size={16} /> {toast}</div>}
    </main>
  );
}

const playerCards = [
  {
    id: "favour",
    tag: "FAVOUR",
    handle: "NIM • Favour",
    rating: 88,
    role: "OBJ",
    initials: "FV",
    rarity: "Elite Series",
    form: "+3 this season",
    attributes: [
      ["SLY", 84], ["OBJ", 94], ["AIM", 87], ["IQ", 91], ["COM", 90], ["CLT", 85],
    ],
    detail: { kd: "1.14", hill: "91.2s", win: "72%", maps: "34" },
  },
  {
    id: "sly",
    tag: "SLY",
    handle: "NIM • Sly",
    rating: 86,
    role: "SMG",
    initials: "SL",
    rarity: "Elite Series",
    form: "+2 this season",
    attributes: [
      ["SLY", 92], ["OBJ", 78], ["AIM", 90], ["IQ", 83], ["COM", 84], ["CLT", 88],
    ],
    detail: { kd: "1.28", hill: "43.8s", win: "69%", maps: "31" },
  },
  {
    id: "reign",
    tag: "REIGN",
    handle: "NIM • Reign",
    rating: 85,
    role: "AR",
    initials: "RG",
    rarity: "Pro Series",
    form: "+4 this season",
    attributes: [
      ["SLY", 88], ["OBJ", 81], ["AIM", 92], ["IQ", 87], ["COM", 80], ["CLT", 84],
    ],
    detail: { kd: "1.31", hill: "48.1s", win: "68%", maps: "29" },
  },
  {
    id: "void",
    tag: "VOID",
    handle: "NIM • Void",
    rating: 83,
    role: "SNIPER",
    initials: "VD",
    rarity: "Pro Series",
    form: "+1 this season",
    attributes: [
      ["SLY", 79], ["OBJ", 72], ["AIM", 95], ["IQ", 88], ["COM", 82], ["CLT", 90],
    ],
    detail: { kd: "1.22", hill: "18.5s", win: "65%", maps: "26" },
  },
];

function PlayerCardsView({ onAction }: { onAction: (message: string) => void }) {
  const [selectedId, setSelectedId] = useState(playerCards[0].id);
  const selected = playerCards.find((player) => player.id === selectedId) ?? playerCards[0];

  return (
    <div className="cardsView">
      <section className="cardShowcase panel">
        <div className="showcaseCopy">
          <span className="livePill"><i /> VERIFIED CARD</span>
          <h2>Your season. Your card.</h2>
          <p>Every rating is built from verified competition results, recent form and the impact of your role—not popularity.</p>
          <div className="cardMeta">
            <div><span>Card edition</span><strong>West Africa S4</strong></div>
            <div><span>Last updated</span><strong>Today · 06:20</strong></div>
          </div>
          <div className="showcaseActions">
            <button className="primaryButton" onClick={() => onAction(`${selected.handle} card shared`)}><Send size={16} /> Share card</button>
            <button className="secondaryButton" onClick={() => onAction("Card image prepared")}>Export image</button>
          </div>
        </div>

        <div className="playerCardStage" aria-live="polite">
          <article className={`ultimateCard ${selected.rarity === "Pro Series" ? "proCard" : ""}`} aria-label={`${selected.handle}, ${selected.rating} rated ${selected.role}`}>
            <div className="cardGlint" />
            <div className="cardTop">
              <div className="overall"><strong>{selected.rating}</strong><span>{selected.role}</span><i /></div>
              <div className="cardEdition"><Zap size={13} fill="currentColor" /><span>SH</span></div>
            </div>
            <div className="playerPortrait"><span>{selected.initials}</span><i /></div>
            <div className="cardIdentity">
              <span className="cardTeam">N¡M ESPORTS</span>
              <h3>{selected.tag}</h3>
              <p><span>🇳🇬</span> West Africa · S4</p>
            </div>
            <div className="cardAttributes">
              {selected.attributes.map(([label, value]) => (
                <div key={label}><strong>{value}</strong><span>{label}</span></div>
              ))}
            </div>
            <div className="cardFooter"><BadgeCheck size={13} /><span>SQUADHUB VERIFIED</span><b>04</b></div>
          </article>
        </div>
      </section>

      <section className="cardData panel">
        <div className="viewHeader">
          <div><span className="panelKicker">CARD BREAKDOWN</span><h2>{selected.handle}</h2><p>{selected.rarity} · {selected.form}</p></div>
          <span className="ratingMovement"><TrendingUp size={14} /> In form</span>
        </div>
        <div className="cardDataStats">
          <div><span>K/D</span><strong>{selected.detail.kd}</strong><small>Official matches</small></div>
          <div><span>OBJ / MAP</span><strong>{selected.detail.hill}</strong><small>Hardpoint average</small></div>
          <div><span>MAP WIN</span><strong>{selected.detail.win}</strong><small>Last 30 days</small></div>
          <div><span>MAPS</span><strong>{selected.detail.maps}</strong><small>Rating sample</small></div>
        </div>
        <div className="ratingNote"><Shield size={17} /><p><strong>How the rating works</strong><span>Weighted by role, opponent strength and competition tier. Scrims never affect official cards.</span></p><button className="textButton">Methodology</button></div>
      </section>

      <section className="cardCollection panel">
        <div className="viewHeader"><div><span className="panelKicker">N¡M COLLECTION</span><h2>Player cards</h2><p>Select a player to inspect their live card.</p></div><span className="collectionCount">{playerCards.length} / 7 issued</span></div>
        <div className="cardPicker">
          {playerCards.map((player) => (
            <button className={`miniPlayerCard ${selected.id === player.id ? "selected" : ""}`} key={player.id} onClick={() => setSelectedId(player.id)} aria-pressed={selected.id === player.id}>
              <span className="miniRating">{player.rating}</span>
              <span className="miniAvatar">{player.initials}</span>
              <span className="miniName">{player.tag}</span>
              <small>{player.role} · {player.rarity.replace(" Series", "")}</small>
            </button>
          ))}
          <button className="miniPlayerCard locked" onClick={() => onAction("Three cards unlock after 10 verified maps")}>
            <span className="miniRating">—</span><span className="miniAvatar"><Shield size={18} /></span><span className="miniName">LOCKED</span><small>10 verified maps</small>
          </button>
        </div>
      </section>
    </div>
  );
}

function Dashboard({ onAction }: { onAction: (message: string) => void }) {
  return (
    <div className="dashboardGrid">
      <section className="liveCard panel">
        <div className="panelHeader">
          <div><span className="livePill"><i /> NEXT UP</span><h2>Scrim block</h2></div>
          <span className="timePill">Starts in 02:14:38</span>
        </div>
        <div className="matchup">
          <div className="club"><div className="largeCrest nim">N¡M</div><strong>N¡M Esports</strong><span>West Africa #8</span></div>
          <div className="versus"><span>BEST OF 5</span><b>VS</b><small>Private lobby</small></div>
          <div className="club"><div className="largeCrest elite">LE</div><strong>Lagos Elite</strong><span>West Africa #3</span></div>
        </div>
        <div className="modeStrip">
          <span><b>1</b> Hardpoint · Summit</span>
          <span><b>2</b> S&amp;D · Firing Range</span>
          <span><b>3</b> Control · Raid</span>
        </div>
        <div className="cardActions">
          <button className="primaryButton" onClick={() => onAction("Match room is ready")}><Swords size={17} /> Open match room</button>
          <button className="secondaryButton" onClick={() => onAction("Game plan opened")}>View game plan</button>
        </div>
      </section>

      <section className="recordCard panel">
        <div className="panelHeader compact"><div><span className="panelKicker">CURRENT FORM</span><h2>Season record</h2></div><button className="textButton">Details</button></div>
        <div className="recordScore"><strong>14–6</strong><span>70% win rate</span></div>
        <div className="formRow"><span>LAST 5</span><i className="win">W</i><i className="win">W</i><i className="loss">L</i><i className="win">W</i><i className="win">W</i></div>
        <div className="statSplit"><div><span>HP record</span><strong>8–2</strong></div><div><span>S&amp;D record</span><strong>4–3</strong></div><div><span>Control</span><strong>2–1</strong></div></div>
      </section>

      <section className="lineupCard panel">
        <div className="panelHeader compact"><div><span className="panelKicker">TONIGHT</span><h2>Starting five</h2></div><span className="readyCount">4 / 5 ready</span></div>
        <div className="players">
          {lineup.map((player) => (
            <div className="playerRow" key={player.tag}>
              <div className="playerAvatar">{player.initials}</div>
              <div><strong>{player.tag}</strong><span>{player.role}</span></div>
              <span className={`status ${player.status.toLowerCase()}`}><i /> {player.status}</span>
            </div>
          ))}
        </div>
        <button className="fullButton" onClick={() => onAction("Lineup check sent to the squad")}>Send readiness check</button>
      </section>

      <section className="scheduleCard panel">
        <div className="panelHeader compact"><div><span className="panelKicker">THIS WEEK</span><h2>Schedule</h2></div><button className="iconButton"><CalendarDays size={18} /></button></div>
        <div className="scheduleList">
          {schedule.map((item) => (
            <div className="scheduleItem" key={item.title}>
              <div className={`scheduleTime ${item.accent}`}>{item.time}</div>
              <div><strong>{item.title}</strong><span>{item.meta}</span></div>
              <ChevronDown size={16} className="rotate" />
            </div>
          ))}
        </div>
        <button className="fullButton">Open full calendar</button>
      </section>

      <section className="activityCard panel">
        <div className="panelHeader compact"><div><span className="panelKicker">SQUAD FEED</span><h2>Latest activity</h2></div><button className="textButton">View all</button></div>
        <div className="feed">
          <div><span className="feedIcon result"><Trophy size={15} /></span><p><strong>Result verified</strong>N¡M defeated Abuja Force 3–1</p><time>2h</time></div>
          <div><span className="feedIcon roster"><Users size={15} /></span><p><strong>Roster updated</strong>Void moved into the starting lineup</p><time>5h</time></div>
          <div><span className="feedIcon transfer"><WalletCards size={15} /></span><p><strong>New transfer offer</strong>Royal Ravens submitted a bid for Reign</p><time>1d</time></div>
        </div>
      </section>
    </div>
  );
}

const rosterTiers = [
  { id: "T1", name: "First Team", subtitle: "Premier competition roster", count: 7, color: "#c9ff4a", players: ["Favour", "Sly", "Reign", "Kage", "Void", "Flux", "Zero"] },
  { id: "T2", name: "Second Team", subtitle: "Challenger roster", count: 6, color: "#9cc7ff", players: ["Rogue", "Vex", "Mako", "Nova", "Ace", "Jinx"] },
  { id: "T3", name: "Academy", subtitle: "High-potential prospects", count: 5, color: "#ffc77e", players: ["Kyro", "Miz", "Kane", "Lex", "Rai"] },
  { id: "T4", name: "Development", subtitle: "Youth and new talent", count: 4, color: "#d8c0ff", players: ["Neo", "Sol", "Frost", "Lynx"] },
];

function ClubView({ onInvite, onAction }: { onInvite: () => void; onAction: (message: string) => void }) {
  const [tierId, setTierId] = useState("T1");
  const tier = rosterTiers.find((item) => item.id === tierId) ?? rosterTiers[0];
  return (
    <div className="productStack">
      <section className="panel clubHero">
        <div className="clubHeroIdentity"><div className="largeCrest nim">N¡M</div><div><span className="verified"><BadgeCheck size={14} /> Verified organization</span><h2>N¡M Esports</h2><p>Four connected roster tiers · 22 registered players</p></div></div>
        <div className="clubHeroStats"><div><span>Club value</span><strong>₦4.82M</strong></div><div><span>Power rank</span><strong>#8 WA</strong></div><div><span>Roster health</span><strong>92%</strong></div></div>
        <button className="primaryButton" onClick={onInvite}><UserPlus size={16} /> Invite player</button>
      </section>

      <section className="tierGrid" aria-label="Club roster structure">
        {rosterTiers.map((item) => <button key={item.id} className={`tierCard ${tierId === item.id ? "selected" : ""}`} onClick={() => setTierId(item.id)} style={{ "--tier": item.color } as React.CSSProperties}><span>{item.id}</span><div><strong>{item.name}</strong><small>{item.subtitle}</small></div><b>{item.count}</b></button>)}
      </section>

      <div className="twoColumnProduct">
        <section className="panel">
          <div className="viewHeader"><div><span className="panelKicker">{tier.id} ROSTER</span><h2>{tier.name}</h2><p>{tier.count} players registered for West Africa S4</p></div><button className="secondaryButton" onClick={() => onAction(`${tier.name} lineup submitted`)}><ShieldCheck size={15} /> Submit roster</button></div>
          <div className="peopleTable">
            {tier.players.map((name, index) => <div key={name}><span className="playerAvatar">{name.slice(0,2).toUpperCase()}</span><p><strong>NIM • {name}</strong><small>{index === 0 ? "Captain · OBJ" : ["SMG Slayer", "Main AR", "Flex", "Sniper"][index % 4]}</small></p><span className="contractTag">{index === tier.players.length - 1 ? "Trial" : "Contracted"}</span><strong>{index === 0 ? "₦620k" : `₦${460 - index * 35}k`}</strong><button className="rowAction" onClick={() => onAction(`${name}'s player profile opened`)}>View</button></div>)}
          </div>
        </section>

        <aside className="productRail">
          <section className="panel timelinePanel"><div className="viewHeader"><div><span className="panelKicker">PLAYER TIMELINE</span><h2>Kyro’s pathway</h2><p>Every move stays on the career record.</p></div><History size={18} /></div><div className="careerLine"><article><i /><time>08 Aug 2026</time><strong>Promoted to T3 Academy</strong><p>Approved by Favour I. · Effective immediately</p></article><article><i /><time>12 May 2026</time><strong>Joined T4 Development</strong><p>Free-agent signing · 12-month contract</p></article><article><i /><time>28 Apr 2026</time><strong>Trial completed</strong><p>8 scrims · 7.6 staff rating</p></article></div></section>
          <section className="panel pathwayCard"><Crown size={19} /><div><span className="panelKicker">PATHWAY ACTION</span><strong>Kyro is promotion-eligible</strong><p>Academy requirements met: 12 official maps, conduct clear, guardian consent valid.</p></div><button className="primaryButton" onClick={() => onAction("Promotion request sent for approval")}>Promote</button></section>
        </aside>
      </div>
    </div>
  );
}

function MarketView({ status, setStatus, onAction }: { status: Record<string, string>; setStatus: (next: Record<string, string>) => void; onAction: (message: string) => void }) {
  const [tab, setTab] = useState("Offers");
  const offers = [
    { id: "o1", club: "Royal Ravens", player: "NIM • Reign", type: "Permanent · Public", amount: "₦500,000", expiry: "2d 14h", logo: "RR" },
    { id: "o2", club: "Lagos Elite", player: "NIM • Void", type: "Season loan · Private", amount: "₦120,000", expiry: "18h", logo: "LE" },
    { id: "o3", club: "Night Wolves", player: "NIM • Flux", type: "Permanent · Public", amount: "₦280,000", expiry: "4d 3h", logo: "NW" },
  ];
  const decide = (id: string, next: string, club: string) => { setStatus({ ...status, [id]: next }); onAction(`${club} offer ${next.toLowerCase()}`); };
  return <div className="productStack">
    <section className="marketSummary"><div><span>Transfer window</span><strong>Open · 21 days</strong><small>Closes 31 August, 23:59 WAT</small></div><div><span>Club market value</span><strong>₦4.82M</strong><small>↑ 8.4% this season</small></div><div><span>Registration status</span><strong>Compliant</strong><small>22 of 24 slots used</small></div></section>
    <div className="sectionTabs" role="tablist">{["Offers","Player market","Contracts","Window rules"].map((item) => <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>{item}{item === "Offers" && <small>3</small>}</button>)}</div>
    {tab === "Offers" && <div className="twoColumnProduct"><section className="panel"><div className="viewHeader"><div><span className="panelKicker">NEGOTIATION ROOM</span><h2>Live offers</h2><p>Accept, reject or counter before each deadline.</p></div><button className="primaryButton" onClick={() => onAction("New transfer offer draft created")}><Plus size={15} /> Make offer</button></div><div className="offerList">{offers.map((offer) => <article className="offer" key={offer.id}><div className="offerLogo">{offer.logo}</div><div className="offerMain"><span>{offer.club}</span><strong>{offer.player}</strong><small>{offer.type} · Expires {offer.expiry}</small></div><div className="offerAmount"><span>Guaranteed fee</span><strong>{offer.amount}</strong></div>{status[offer.id] ? <span className={`decision ${status[offer.id].toLowerCase()}`}><Check size={14} /> {status[offer.id]}</span> : <div className="offerActions"><button onClick={() => decide(offer.id,"Declined",offer.club)}>Reject</button><button onClick={() => decide(offer.id,"Countered",offer.club)}>Counter</button><button onClick={() => decide(offer.id,"Accepted",offer.club)}>Accept</button></div>}</article>)}</div></section><aside className="productRail"><section className="panel dealGuard"><ShieldCheck size={22} /><h3>Deal guard</h3><ul><li><Check size={13} /> Player consent attached</li><li><Check size={13} /> Naira-only fee validated</li><li><Check size={13} /> Buyout clause checked</li><li><Check size={13} /> Window registration allowed</li></ul></section><section className="panel deadlineCard"><TimerReset size={20} /><div><span>Next deadline</span><strong>Lagos Elite loan</strong><small>18h 04m remaining</small></div></section></aside></div>}
    {tab === "Player market" && <section className="panel"><div className="viewHeader"><div><span className="panelKicker">AFRICAN PLAYER MARKET</span><h2>Available talent</h2><p>Verified profiles, transparent status and naira valuations.</p></div><button className="secondaryButton"><Search size={15} /> Filters</button></div><div className="marketPlayers">{[["Toxic","SMG","Free agent","₦420k","Nigeria"],["Killa","IGL / AR","Buyout: ₦650k","₦580k","Ghana"],["Saint","BR Slayer","Loan listed","₦370k","Kenya"],["Zed","Flex","Contract expires in 32d","₦290k","Nigeria"]].map((p) => <article key={p[0]}><span className="marketAvatar">{p[0].slice(0,2)}</span><div><strong>{p[0]}</strong><small>{p[1]} · {p[4]}</small></div><span className="listingStatus">{p[2]}</span><strong>{p[3]}</strong><button onClick={() => onAction(`Private offer started for ${p[0]}`)}>Approach</button></article>)}</div></section>}
    {tab === "Contracts" && <section className="panel"><div className="viewHeader"><div><span className="panelKicker">CONTRACT REGISTER</span><h2>Squad contracts</h2><p>Expiry dates, values and buyout protection.</p></div><button className="primaryButton" onClick={() => onAction("Contract draft created")}><Plus size={15}/> New contract</button></div><div className="contractGrid">{[["Favour","30 Jun 2027","₦620k","₦1.2M"],["Reign","31 Dec 2026","₦500k","₦850k"],["Void","31 Aug 2026","₦410k","None"],["Kyro","12 May 2027","₦180k","₦350k"]].map((c) => <article key={c[0]}><span>{c[0]}</span><small>Expires</small><strong>{c[1]}</strong><small>Value / Buyout</small><b>{c[2]} · {c[3]}</b></article>)}</div></section>}
    {tab === "Window rules" && <WindowControl onAction={onAction} />}
  </div>;
}

function WindowControl({ onAction }: { onAction: (message: string) => void }) {
  const phases = [{name:"Registration",date:"1–10 Aug",state:"Complete"},{name:"Transfer window",date:"11–31 Aug",state:"Open"},{name:"Roster lock",date:"1 Sep",state:"Scheduled"},{name:"Emergency stand-ins",date:"Organizer approval",state:"Restricted"}];
  return <div className="twoColumnProduct"><section className="panel"><div className="viewHeader"><div><span className="panelKicker">ORGANIZER CONTROLS</span><h2>NCS Season 4 window</h2><p>Rules apply automatically to every registered club.</p></div><span className="verified"><BadgeCheck size={14}/> Published</span></div><div className="phaseList">{phases.map((p, i) => <article key={p.name}><span>{String(i+1).padStart(2,"0")}</span><div><strong>{p.name}</strong><small>{p.date}</small></div><b className={p.state.toLowerCase().replace(" ","")}>{p.state}</b></article>)}</div></section><aside className="productRail"><section className="panel ruleCard"><h3>After roster lock</h3><p>Unrestricted transfers stop. Clubs must file an emergency or late-registration request with evidence.</p><button className="primaryButton" onClick={() => onAction("Emergency stand-in request opened")}>Request exception</button></section><section className="panel ruleCard"><h3>Current limits</h3><dl><div><dt>Roster</dt><dd>5–8 players</dd></div><div><dt>Stand-ins</dt><dd>1 emergency</dd></div><div><dt>Late fee</dt><dd>₦15,000</dd></div></dl></section></aside></div>;
}

function CompetitionView({ onAction }: { onAction: (message: string) => void }) {
  const [mode, setMode] = useState("Multiplayer");
  const [organizerOpen, setOrganizerOpen] = useState(false);
  const standings = [
    ["1", "Lagos Elite", "12", "10", "2", "30"], ["2", "Royal Ravens", "12", "9", "3", "27"],
    ["3", "Night Wolves", "12", "8", "4", "24"], ["4", "N¡M Esports", "12", "7", "5", "21"],
    ["5", "Abuja Force", "12", "6", "6", "18"], ["6", "Kano Storm", "12", "4", "8", "12"],
  ];
  return (
    <div className="productStack">
      <div className="competitionToolbar"><div className="sectionTabs"><button className={mode === "Multiplayer" ? "active" : ""} onClick={() => setMode("Multiplayer")}><Crosshair size={14}/> Multiplayer</button><button className={mode === "Battle Royale" ? "active" : ""} onClick={() => setMode("Battle Royale")}><MapPin size={14}/> Battle Royale</button></div><button className="secondaryButton" onClick={() => setOrganizerOpen((v) => !v)}><Settings size={15}/> Organizer console</button></div>
      {organizerOpen && <section className="panel organizerConsole"><div><span className="panelKicker">TOURNAMENT CONTROL</span><h2>Registration & roster policy</h2><p>Changes publish to every registered club and are preserved in the audit log.</p></div><div className="organizerSettings"><label>Roster lock<select defaultValue="1-sep"><option value="1-sep">1 Sep · 23:59 WAT</option></select></label><label>Emergency stand-ins<select defaultValue="approval"><option value="approval">Organizer approval</option><option value="off">Not allowed</option></select></label><label>Late registration<select defaultValue="fee"><option value="fee">Allowed · ₦15,000 fee</option><option value="off">Not allowed</option></select></label><button className="primaryButton" onClick={() => onAction("Tournament policy published")}>Publish rules</button></div></section>}
      <div className="viewGrid competitionView">
      <section className="panel tournamentHero">
        <div className="competitionLogo"><Trophy size={27} /></div>
        <div><span className="livePill"><i /> LIVE SEASON</span><h2>{mode === "Multiplayer" ? "Nigeria Championship Series" : "West Africa BR League"}</h2><p>{mode === "Multiplayer" ? "Regular season · Matchday 12 of 16" : "Series 5 of 8 · 16 squads"}</p></div>
        <button className="secondaryButton" onClick={() => onAction("Competition followed")}>Follow competition</button>
      </section>
      <section className="panel standingsPanel">
        <div className="viewHeader"><div><span className="panelKicker">{mode === "Multiplayer" ? "LEAGUE TABLE" : "SERIES STANDINGS"}</span><h2>West division</h2><p>{mode === "Multiplayer" ? "Top four advance to playoffs." : "Placement and eliminations combined."}</p></div><button className="textButton">Ranking rules</button></div>
        <div className="standingTable">
          <div className="standingHead"><span>#</span><span>Team</span><span>P</span><span>W</span><span>L</span><span>PTS</span></div>
          {standings.map((row) => <div className={`standingRow ${row[1] === "N¡M Esports" ? "isNim" : ""}`} key={row[1]}>{row.map((cell, index) => <span key={index}>{cell}</span>)}</div>)}
        </div>
      </section>
      <aside className="viewRail fixturesRail">
        <section className="panel"><div className="panelHeader compact"><div><span className="panelKicker">UP NEXT</span><h2>Fixtures</h2></div><CalendarDays size={18} /></div><div className="fixture"><span>FRI · 19:00</span><div><strong>N¡M</strong><b>vs</b><strong>Night Wolves</strong></div><small>Round 13 · Best of 5</small></div><div className="fixture"><span>SUN · 20:30</span><div><strong>Royal Ravens</strong><b>vs</b><strong>N¡M</strong></div><small>Round 14 · Best of 5</small></div></section>
        <section className="panel prizeCard"><span className="panelKicker">PRIZE POOL</span><strong>₦2.5M</strong><p>Champions take ₦1.2M plus a West Africa Masters seed.</p></section>
      </aside></div>
    </div>
  );
}

function IntegrityView({ onAction }: { onAction: (message: string) => void }) {
  const [recordType, setRecordType] = useState("Official");
  const [caseState, setCaseState] = useState("Under review");
  const records: Record<string, string[][]> = {
    Official: [["NCS S4 · Round 12","N¡M 3–1 Abuja Force","Verified","09 Aug"],["NCS S4 · Round 11","Royal Ravens 3–2 N¡M","Verified","03 Aug"],["WA Masters Qualifier","N¡M 2–3 Night Wolves","Disputed","28 Jul"]],
    Scrims: [["Practice block","N¡M 4–1 Lagos Elite","Team-only","10 Aug"],["Practice block","N¡M 2–3 Revenant","Team-only","07 Aug"]],
    Challenges: [["₦50k challenge","N¡M 3–0 Toxic Unit","Community","01 Aug"],["Showmatch","N¡M 2–2 Abuja Force","Community","20 Jul"]],
  };
  return <div className="productStack"><section className="integrityBanner panel"><div><ShieldCheck size={24}/><span><strong>Official record separation is active</strong><small>Scrims and challenges can never change league tables, power rankings or player cards.</small></span></div><button className="secondaryButton" onClick={() => onAction("Integrity policy opened")}>View policy</button></section><div className="twoColumnProduct"><section className="panel"><div className="viewHeader"><div><span className="panelKicker">RESULTS REGISTER</span><h2>Match records</h2><p>One source of truth, clearly classified.</p></div><button className="primaryButton" onClick={() => onAction("Result submission opened")}><Plus size={15}/> Submit result</button></div><div className="recordSwitcher">{Object.keys(records).map((item) => <button key={item} onClick={() => setRecordType(item)} className={recordType === item ? "active" : ""}>{item}</button>)}</div><div className="resultLedger">{records[recordType].map((r) => <article key={r[0]+r[1]}><span className={`recordDot ${recordType.toLowerCase()}`}/><div><small>{r[0]}</small><strong>{r[1]}</strong></div><b className={r[2].toLowerCase().replace("-","")}>{r[2]}</b><time>{r[3]}</time></article>)}</div></section><aside className="productRail"><section className="panel disputeCard"><div className="viewHeader"><div><span className="panelKicker">OPEN CASE</span><h2>DIS-2048</h2></div><span className="caseState">{caseState}</span></div><div className="caseBody"><span>Match dispute</span><strong>WA Masters: N¡M vs Night Wolves</strong><p>N¡M alleges an ineligible emergency stand-in was used after roster lock.</p><dl><div><dt>Evidence</dt><dd>4 files</dd></div><div><dt>Response due</dt><dd>11h 42m</dd></div><div><dt>Assigned to</dt><dd>NCS Integrity</dd></div></dl><button className="primaryButton" onClick={() => {setCaseState("Evidence added"); onAction("Evidence added to DIS-2048")}}><FileText size={15}/> Add evidence</button></div></section><section className="panel disputeTypes"><h3>Dispute coverage</h3><p><Gavel size={14}/> Match & eligibility</p><p><ArrowRightLeft size={14}/> Transfer & contract</p><p><Flag size={14}/> Conduct & safeguarding</p></section></aside></div></div>;
}

function RankingsView() {
  const [board, setBoard] = useState<"Pro Players" | "Ranked Mode" | "Streamers" | "Clubs">("Pro Players");
  const [scope, setScope] = useState("West Africa");
  const boards = {
    "Pro Players": {
      kicker: "COMPETITIVE PLAYER INDEX",
      title: `${scope} pro players`,
      description: "Role-adjusted impact from verified official matches only.",
      hero: "#6",
      heroLabel: "Favour · OBJ",
      heroMove: "↑ 3 places this month",
      columns: ["Rank", "Player", "Org / role", "Rating", "Form"],
      rows: [
        ["1", "LE • Raptor", "Lagos Elite · Flex", "92.4", "+1"],
        ["2", "RR • Nyx", "Royal Ravens · SMG", "91.7", "—"],
        ["3", "NW • Ghost", "Night Wolves · AR", "90.8", "+2"],
        ["6", "NIM • Favour", "N¡M Esports · OBJ", "88.9", "+3"],
        ["9", "NIM • Sly", "N¡M Esports · SMG", "86.7", "+1"],
      ],
      note: "Ratings weight role impact, opponent strength, event tier and recent form. Scrims never count.",
    },
    "Ranked Mode": {
      kicker: "PUBLIC RANKED LADDER",
      title: `${scope} ranked players`,
      description: "Verified CODM ranked profiles for the current MP season.",
      hero: "#14",
      heroLabel: "Favour · Legendary",
      heroMove: "12,480 rank points",
      columns: ["Rank", "Player", "Rank", "Points", "Win rate"],
      rows: [
        ["1", "ToxicMamba", "Legendary · 18x", "18,940", "68%"],
        ["2", "PhantomNG", "Legendary · 16x", "17,620", "65%"],
        ["3", "AccraSlayer", "Legendary · 14x", "16,885", "63%"],
        ["14", "NIM • Favour", "Legendary · 9x", "12,480", "59%"],
        ["18", "NIM • Sly", "Legendary · 11x", "11,940", "61%"],
      ],
      note: "Ranked points use linked CODM profile snapshots. Competitive results and popularity do not affect this board.",
    },
    Streamers: {
      kicker: "CREATOR PULSE",
      title: `${scope} CODM streamers`,
      description: "A transparent monthly creator chart—not a competitive skill rating.",
      hero: "#23",
      heroLabel: "Favour · Rising creator",
      heroMove: "↑ 8 this month",
      columns: ["Rank", "Creator", "Platform", "Watch hours", "Growth"],
      rows: [
        ["1", "KingKez", "YouTube", "184K", "+12%"],
        ["2", "Ama Plays", "TikTok LIVE", "161K", "+18%"],
        ["3", "LagosClutch", "YouTube", "144K", "+7%"],
        ["23", "GojoPlays", "YouTube", "18.6K", "+31%"],
        ["28", "SlyLive", "TikTok LIVE", "15.2K", "+22%"],
      ],
      note: "Creator rank combines verified watch hours, live consistency, engagement quality and African CODM coverage.",
    },
    Clubs: {
      kicker: "REGIONAL POWER INDEX",
      title: `${scope} clubs`,
      description: "Official results, opponent strength, recent form and competition tier.",
      hero: "#8",
      heroLabel: "N¡M Esports",
      heroMove: "↑ 4 places this month",
      columns: ["Rank", "Club", "Region", "Rating", "Move"],
      rows: [
        ["1", "Lagos Elite", "Nigeria", "1,842", "+2"],
        ["2", "Royal Ravens", "Ghana", "1,790", "—"],
        ["3", "Night Wolves", "Nigeria", "1,744", "-1"],
        ["8", "N¡M Esports", "Nigeria", "1,526", "+4"],
        ["12", "Abuja Force", "Nigeria", "1,410", "-2"],
      ],
      note: "Club power uses verified official results. Scrims, challenges and fan votes never count.",
    },
  } as const;
  const currentBoard = boards[board];
  const isHighlighted = (name: string) => name.includes("Favour") || name.includes("Gojo") || name === "N¡M Esports";

  return <div className="productStack rankingsHub">
    <section className="rankingHero panel">
      <div><span className="livePill"><i/> LIVE RANKING NETWORK</span><p className="rankSeason">SQUADHUB · WEST AFRICA S4</p><h2>Every kind of greatness gets its own table.</h2><p>Pro performance, public ranked play, creator impact and club strength are measured separately—so the numbers mean something.</p></div>
      <div className="rankHeroNumber"><span>{currentBoard.heroLabel}</span><strong>{currentBoard.hero}</strong><small>{currentBoard.heroMove}</small></div>
    </section>

    <div className="rankingBoardTabs" role="tablist" aria-label="Ranking categories">
      {(["Pro Players", "Ranked Mode", "Streamers", "Clubs"] as const).map((item, index) => <button role="tab" aria-selected={board === item} className={board === item ? "active" : ""} key={item} onClick={() => setBoard(item)}><span>0{index + 1}</span>{item}</button>)}
    </div>

    <div className="rankingTools"><div className="sectionTabs">{["West Africa","Nigeria","Ghana","East Africa"].map((item) => <button className={scope === item ? "active" : ""} key={item} onClick={() => setScope(item)}>{item}</button>)}</div><span>{board === "Streamers" ? "AUGUST CREATOR PULSE" : "MP · SEASON 4"}</span></div>

    <div className="rankingMainGrid">
      <section className="panel rankingTablePanel">
        <div className="viewHeader"><div><span className="panelKicker">{currentBoard.kicker}</span><h2>{currentBoard.title}</h2><p>{currentBoard.description}</p></div><button className="textButton">Scoring rules</button></div>
        <div className="powerTable rankingTable">
          <div className="powerHead">{currentBoard.columns.map((cell, index) => <span key={`${cell}-${index}`}>{cell}</span>)}</div>
          {currentBoard.rows.map((row) => <div key={row[1]} className={isHighlighted(row[1]) ? "highlight" : ""}>{row.map((cell, index) => <span key={index}>{index === 0 && Number(cell) <= 3 ? <b className={`rankMedal medal${cell}`}>{cell}</b> : cell}</span>)}</div>)}
        </div>
        <div className="rankingMethod"><ShieldCheck size={17}/><p><strong>Explainable by design.</strong><span>{currentBoard.note}</span></p></div>
      </section>

      <aside className="rankingRail">
        <section className="panel rankSpotlight"><span className="panelKicker">YOUR SNAPSHOT</span><div className="spotlightAvatar">FI</div><h3>{currentBoard.heroLabel}</h3><strong>{currentBoard.hero}</strong><p>{currentBoard.heroMove}</p><div><span>Verified data</span><b>ACTIVE</b></div></section>
        <section className="panel ladderCard"><span className="panelKicker">NEXT TARGET</span><strong>{board === "Streamers" ? "#20" : board === "Ranked Mode" ? "#10" : "Top 5"}</strong><p>{board === "Streamers" ? "2.4K more monthly watch hours" : board === "Ranked Mode" ? "940 points away" : "Two strong official series"}</p><div><span>Progress</span><i><b style={{width: board === "Streamers" ? "64%" : "72%"}}/></i></div></section>
      </aside>
    </div>
  </div>;
}

function PrestigeView({ onAction }: { onAction: (message: string) => void }) {
  const [profile, setProfile] = useState("Club");
  return <div className="productStack"><div className="sectionTabs"><button className={profile === "Club" ? "active" : ""} onClick={() => setProfile("Club")}>Club cabinet</button><button className={profile === "Player" ? "active" : ""} onClick={() => setProfile("Player")}>Player career</button></div>{profile === "Club" ? <><section className="cabinetHero panel"><div className="largeCrest nim">N¡M</div><div><span className="panelKicker">TROPHY CABINET</span><h2>N¡M Esports</h2><p>6 trophies · 14 podiums · Since 2024</p></div><div className="cabinetValue"><span>Legacy score</span><strong>782</strong><small>West Africa #16</small></div></section><section className="trophyShelf">{[["NCS Cup","Champions","2026","gold"],["Lagos Invitational","Runner-up","2026","silver"],["Naija Pro League","Champions","2025","gold"],["West Open","3rd place","2025","bronze"]].map((t) => <article className="panel" key={t[0]}><div className={`trophyIcon ${t[3]}`}><Trophy size={28}/></div><span>{t[2]}</span><strong>{t[0]}</strong><small>{t[1]}</small></article>)}</section></> : <div className="twoColumnProduct"><section className="panel playerLegacy"><div className="legacyTop"><div className="marketAvatar">FV</div><div><span className="verified"><BadgeCheck size={14}/> Verified career</span><h2>NIM • Favour</h2><p>Objective · Nigeria · 18 official events</p></div><strong>88</strong></div><div className="awardStrip">{[["2","Trophies"],["3","MVPs"],["7","Awards"],["64","Official wins"]].map((x) => <div key={x[1]}><strong>{x[0]}</strong><span>{x[1]}</span></div>)}</div><div className="careerLine"><article><i/><time>August 2026</time><strong>NCS Player of the Week</strong><p>91.2s average hill time · 72% map win rate</p></article><article><i/><time>May 2026</time><strong>Promoted to N¡M First Team</strong><p>T2 Second Team → T1 First Team</p></article><article><i/><time>December 2025</time><strong>Naija Pro League champion</strong><p>Finals MVP · N¡M defeated Royal Ravens 4–2</p></article></div></section><aside className="productRail"><section className="panel awardCard"><Medal size={26}/><h3>Objective Maestro</h3><p>Top 5% objective impact in official West African competitions.</p><button className="secondaryButton" onClick={() => onAction("Achievement shared")}>Share achievement</button></section></aside></div>}</div>;
}

function IdentityView({ onAction }: { onAction: (message: string) => void }) {
  const [step, setStep] = useState<"phone"|"otp"|"profile"|"guardian"|"done">("phone");
  const [phone, setPhone] = useState("+234 ");
  const [age, setAge] = useState("18+");
  const nextFromProfile = () => setStep(age === "Under 18" ? "guardian" : "done");
  return <div className="identityLayout"><section className="identityPitch"><span className="livePill"><i/> STANDALONE ACCESS</span><h2>No Discord required.</h2><p>Every player gets a portable identity tied to a verified phone number—not a server membership that disappears when they change teams.</p><div className="identityPromises"><div><ShieldCheck size={19}/><span><strong>One person, one record</strong><small>Transfers, trophies and conduct follow the verified player.</small></span></div><div><Users size={19}/><span><strong>Protected young players</strong><small>Guardian approval is required before contracts and transfers.</small></span></div><div><BadgeCheck size={19}/><span><strong>Role-based access</strong><small>Player, manager, coach, organizer and integrity roles.</small></span></div></div></section><section className="panel authFlow"><div className="authSteps">{["Phone","Verify","Profile","Safety"].map((s,i) => <span className={i <= ({phone:0,otp:1,profile:2,guardian:3,done:4}[step]) ? "active" : ""} key={s}>{i+1}<small>{s}</small></span>)}</div>{step === "phone" && <div className="authBody"><div className="authIcon"><Shield size={23}/></div><span className="panelKicker">CREATE YOUR SQUADHUB ID</span><h2>Enter your phone number</h2><p>We’ll send a one-time code. Nigerian numbers are shown here, with more African regions supported at launch.</p><label>Mobile number<input value={phone} onChange={(e) => setPhone(e.target.value)} inputMode="tel"/></label><button className="primaryButton" disabled={phone.length < 10} onClick={() => {setStep("otp"); onAction("Verification code sent")}}>Send OTP</button></div>}{step === "otp" && <div className="authBody"><div className="authIcon"><Gamepad2 size={23}/></div><span className="panelKicker">VERIFY NUMBER</span><h2>Enter the 6-digit code</h2><p>Code sent to {phone}. For this product demo, any six digits continue.</p><label>One-time code<input className="otpInput" maxLength={6} placeholder="• • • • • •" onChange={(e) => e.target.value.length === 6 && setStep("profile")}/></label><button className="textButton" onClick={() => onAction("A new code was sent")}>Resend code</button></div>}{step === "profile" && <div className="authBody"><span className="panelKicker">PLAYER PROFILE</span><h2>Set up your competitive identity</h2><label>CODM gamertag<input placeholder="e.g. NIM • Favour"/></label><label>Primary mode<select><option>Multiplayer</option><option>Battle Royale</option><option>Both MP & BR</option></select></label><label>Age group<select value={age} onChange={(e) => setAge(e.target.value)}><option>18+</option><option>Under 18</option></select></label><button className="primaryButton" onClick={nextFromProfile}>Continue</button></div>}{step === "guardian" && <div className="authBody"><span className="panelKicker">GUARDIAN CONSENT</span><h2>Add a parent or guardian</h2><p>They must approve roster registration, contracts and transfers before the account becomes eligible.</p><label>Guardian phone<input placeholder="+234 800 000 0000"/></label><label>Relationship<select><option>Parent</option><option>Legal guardian</option></select></label><button className="primaryButton" onClick={() => {setStep("done"); onAction("Guardian consent request sent")}}>Send consent request</button></div>}{step === "done" && <div className="authBody authDone"><div className="authIcon"><Check size={24}/></div><span className="panelKicker">IDENTITY READY</span><h2>Your SquadHub ID is protected.</h2><p>{age === "Under 18" ? "Guardian approval is pending. Competitive registration unlocks when consent is verified." : "Phone verified. You can now join a club, register for competitions and build your career record."}</p><button className="primaryButton" onClick={() => setStep("phone")}>Preview again</button></div>}</section></div>;
}

const radarAxes = ["Objective pressure", "Trades", "Survival", "Kills", "Objective", "Consistency"];

function PerformanceRadar({ values, color }: { values: number[]; color: string }) {
  const center = 150;
  const radius = 92;
  const point = (index: number, scale = 1) => {
    const angle = (-90 + index * 60) * Math.PI / 180;
    return [center + Math.cos(angle) * radius * scale, center + Math.sin(angle) * radius * scale];
  };
  const polygon = (scale: number) => radarAxes.map((_, index) => point(index, scale).join(",")).join(" ");
  const scoreShape = values.map((value, index) => point(index, value / 100).join(",")).join(" ");
  const labelPositions = [
    [150, 25, "middle"], [276, 82, "end"], [276, 220, "end"],
    [150, 280, "middle"], [24, 220, "start"], [24, 82, "start"],
  ] as const;

  return <svg className="performanceRadar" viewBox="0 0 300 300" role="img" aria-label={`Performance radar: ${radarAxes.map((axis, index) => `${axis} ${values[index]}`).join(", ")}`}>
    <g className="radarGrid">
      {[.25, .5, .75, 1].map((scale) => <polygon key={scale} points={polygon(scale)} />)}
      {radarAxes.map((_, index) => { const [x, y] = point(index); return <line key={index} x1={center} y1={center} x2={x} y2={y} />; })}
    </g>
    <polygon className="radarScore" points={scoreShape} style={{ "--radar-color": color } as React.CSSProperties} />
    {values.map((value, index) => { const [x, y] = point(index, value / 100); return <circle className="radarPoint" key={index} cx={x} cy={y} r="4" style={{ "--radar-color": color } as React.CSSProperties} />; })}
    {radarAxes.map((axis, index) => <text key={axis} x={labelPositions[index][0]} y={labelPositions[index][1]} textAnchor={labelPositions[index][2]}>{axis}</text>)}
  </svg>;
}

function PerformanceView({ onAction }: { onAction: (message: string) => void }) {
  const [tab, setTab] = useState<"AI Review" | "VOD Room" | "Strat Board" | "Training">("AI Review");
  const [player, setPlayer] = useState("NIM • Favour");
  const [reviewState, setReviewState] = useState<"ready" | "queued">("ready");
  const [vodLocked, setVodLocked] = useState(false);
  const [rating, setRating] = useState("4");
  const [weakness, setWeakness] = useState("Lost opening duels on S&D attack");
  const [priority, setPriority] = useState("First-blood discipline");
  const [selectedStrat, setSelectedStrat] = useState("Summit HP");
  const [stratNoteAdded, setStratNoteAdded] = useState(false);
  const [completedDrills, setCompletedDrills] = useState<number[]>([0]);
  const [drillSet, setDrillSet] = useState(0);

  const performanceTabs = [
    ["AI Review", BrainCircuit], ["VOD Room", Video], ["Strat Board", BookOpen], ["Training", Dumbbell],
  ] as const;
  const players: Record<string, { maps: number; kd: string; obj: string; conversion: string; role: string; grade: string; color: string; radar: number[] }> = {
    "NIM • Favour": { maps: 18, kd: "1.14", obj: "91.2s", conversion: "61%", role: "Objective", grade: "A", color: "#c8ff3d", radar: [96, 85, 66, 82, 100, 83] },
    "NIM • Sly": { maps: 21, kd: "1.28", obj: "43.8s", conversion: "66%", role: "Slayer", grade: "B+", color: "#43a0ff", radar: [72, 85, 66, 92, 63, 83] },
    "NIM • Reign": { maps: 16, kd: "1.19", obj: "38.4s", conversion: "63%", role: "Anchor", grade: "B", color: "#b58cff", radar: [69, 78, 91, 84, 68, 88] },
    "NIM • Kage": { maps: 0, kd: "—", obj: "—", conversion: "—", role: "Flex", grade: "—", color: "#64717c", radar: [0, 0, 0, 0, 0, 0] },
  };
  const current = players[player];
  const eligible = current.maps > 0;
  const drillPools = [
    [
      ["Opening-duel reset", "S&D · 12 min", "Run 10 attack openings; disengage after first contact unless traded."],
      ["Two-man trade lane", "Firing Range · 15 min", "Keep pair spacing below 0.8s through three marked lanes."],
      ["Hill break comms", "Hardpoint · 18 min", "Call utility, entry order and spawn read before every break."],
    ],
    [
      ["Shoulder-peek discipline", "S&D · 10 min", "Collect information without committing the opening death."],
      ["Weak-side spawn read", "Summit · 16 min", "Identify flip risk within three seconds of each respawn."],
      ["Numbers-up closeout", "Control · 15 min", "Convert 4v3 advantages without isolated challenges."],
    ],
  ];
  const drills = drillPools[drillSet];

  const queueReview = () => {
    if (!eligible) { onAction("No review generated: Kage logged zero matches this week"); return; }
    setReviewState("queued");
    window.setTimeout(() => setReviewState("ready"), 1200);
    onAction("Weekly review queued from verified data");
  };
  const toggleDrill = (index: number) => setCompletedDrills((items) => items.includes(index) ? items.filter((item) => item !== index) : [...items, index]);

  return (
    <div className="performanceSuite">
      <section className="performanceHero panel">
        <div>
          <span className="livePill"><i /> PERFORMANCE LAB</span>
          <h2>From match evidence to better habits.</h2>
          <p>Review verified matches, capture coach observations, agree tactics and turn every weakness into a trackable training plan.</p>
        </div>
        <div className="performanceHeroStats">
          <div><span>Review cycle</span><strong>Week 32</strong><small>Closes Sunday · 23:59</small></div>
          <div><span>Squad completion</span><strong>74%</strong><small>18 of 24 drills</small></div>
          <div><span>Next team block</span><strong>20:00</strong><small>Summit rotations</small></div>
        </div>
      </section>

      <div className="performanceNav" role="tablist" aria-label="Performance tools">
        {performanceTabs.map(([label, Icon]) => <button role="tab" aria-selected={tab === label} className={tab === label ? "active" : ""} key={label} onClick={() => setTab(label)}><Icon size={16}/><span>{label}</span></button>)}
      </div>

      {tab === "AI Review" && <div className="performanceProductGrid">
        <section className="panel aiReviewMain">
          <div className="viewHeader aiReviewHeader"><div><span className="panelKicker">WEEKLY PLAYER REVIEW</span><h2>{player}</h2><p>10–16 August · Official matches, scrims and manager observations</p></div><label className="playerSelect">Player<select value={player} onChange={(event) => setPlayer(event.target.value)}>{Object.keys(players).map((name) => <option key={name}>{name}</option>)}</select></label></div>
          <div className="evidenceStrip">
            <article><BadgeCheck size={17}/><span><strong>{current.maps} maps</strong><small>Verified match logs</small></span></article>
            <article><ClipboardCheck size={17}/><span><strong>{eligible ? "3 reviews" : "No reviews"}</strong><small>Manager VOD forms</small></span></article>
            <article><MessageSquare size={17}/><span><strong>{eligible ? "Submitted" : "Missing"}</strong><small>Player self-report</small></span></article>
          </div>
          <section className={`performanceBreakdown ${!eligible ? "isEmpty" : ""}`}>
            <div className="breakdownHeading"><div><span className="panelKicker">PERFORMANCE BREAKDOWN</span><h3>How this week was played</h3><p>Objective pressure · trades · survival · kills · objective · consistency</p></div><span className="teamLabel" style={{ color: current.color }}>N¡M FIRST TEAM</span></div>
            <div className="breakdownPlayer" style={{ "--player-color": current.color } as React.CSSProperties}>
              <div className="breakdownIdentity"><div><strong>{player}</strong><span>{current.role} · {current.maps} verified maps</span></div><b>{current.grade}</b></div>
              {eligible ? <PerformanceRadar values={current.radar} color={current.color} /> : <div className="radarUnavailable"><BarChart3 size={26}/><strong>No verified performance</strong><span>Play a logged match to unlock the breakdown.</span></div>}
              <div className="breakdownStats">{radarAxes.map((axis, index) => <span key={axis}><small>{axis.split(" ").map((word) => word[0]).join("")}</small><strong>{eligible ? current.radar[index] : "—"}</strong></span>)}</div>
            </div>
          </section>
          {!eligible ? <div className="emptyReview"><Clock3 size={25}/><h3>No review this week</h3><p>Kage logged zero matches. SquadHub will not invent a performance review without evidence.</p></div> : reviewState === "queued" ? <div className="reviewGenerating"><RefreshCw size={25}/><h3>Review queued</h3><p>The coach summary is being prepared asynchronously. The player will receive a push notification when it is ready.</p></div> : <div className="coachReview">
            <div className="reviewTitle"><div className="aiBadge"><Sparkles size={18}/></div><div><span>COACH SUMMARY</span><h3>Strong objective week, but protect the opening life.</h3></div><span className="reviewReady"><Check size={12}/> Ready</span></div>
            <p>{player.split(" • ")[1]} created consistent hill pressure and maintained {current.obj} objective time. The clearest loss pattern came after the team conceded first blood on attack. This review only uses the 18 logged maps and three submitted coach forms.</p>
            <div className="reviewStatLine"><div><span>K/D</span><strong>{current.kd}</strong></div><div><span>OBJ / HP</span><strong>{current.obj}</strong></div><div><span>S&amp;D attack</span><strong>{current.conversion}</strong></div><div><span>Evidence</span><strong>{current.maps} maps</strong></div></div>
            <div className="focusGrid"><article><span>01 · PRIORITY</span><strong>{priority}</strong><p>Preserve the opening life when there is no immediate trade setup.</p><small>From VOD notes at 01:12 and 06:48</small></article><article><span>02 · TEAM HABIT</span><strong>Trade spacing</strong><p>Reduce the gap between entry and support during close-range breaks.</p><small>Observed in 7 of 18 maps</small></article><article><span>03 · KEEP</span><strong>Hill discipline</strong><p>Continue early rotations and disciplined anchor handoffs.</p><small>{current.obj} average HP objective time</small></article></div>
          </div>}
          <div className="aiPolicy"><ShieldCheck size={16}/><p><strong>No invented stats.</strong> Every claim links back to a match log, coach form or player self-report.</p><button className="primaryButton" onClick={queueReview} disabled={reviewState === "queued"}>{reviewState === "queued" ? "Generating…" : "Generate new review"}</button></div>
        </section>
        <aside className="performanceRail">
          <section className="panel integrationCard engineCard"><div className="integrationIcon"><BrainCircuit size={22}/></div><span className="panelKicker">SQUADHUB PERFORMANCE ENGINE</span><h3>Rules first. Gemini Flash second.</h3><p>Our engine validates match evidence, finds trends and selects drills. Gemini Flash only turns those verified findings into clear coaching language.</p><ol className="enginePipeline"><li><span>01</span><b>Validate evidence</b></li><li><span>02</span><b>Detect patterns</b></li><li><span>03</span><b>Gemini Flash wording</b></li><li><span>04</span><b>Coach approval</b></li></ol><div><span>Model layer</span><strong>Gemini Flash · ready</strong></div></section>
          <section className="panel cadenceCard"><div className="panelHeader compact"><div><span className="panelKicker">DELIVERY</span><h2>Review cadence</h2></div><Bell size={17}/></div><p><span>Team Pro</span><strong>7-day adaptive</strong></p><p><span>Community</span><strong>2 reviews / week</strong></p><p><span>Zero-match rule</span><strong>Skip review</strong></p></section>
        </aside>
      </div>}

      {tab === "VOD Room" && <div className="performanceProductGrid">
        <section className="panel vodWorkspace">
          <div className="vodToolbar"><div><span className="panelKicker">MANAGER REVIEW</span><h2>N¡M vs Lagos Elite · Summit HP</h2><p>Scrim · 10 August · Match reference #SCR-8102</p></div><span className={vodLocked ? "lockedPill locked" : "lockedPill"}>{vodLocked ? <Check size={13}/> : <Clock3 size={13}/>} {vodLocked ? "Submitted & locked" : "Draft review"}</span></div>
          <div className="vodNotice"><Video size={17}/><p><strong>Review the match in your normal VOD tool.</strong> SquadHub stores structured timestamps and coach notes—not the full video—so analysis stays fast and affordable.</p></div>
          <div className="timestampList">
            {["01:12 · Favour takes opening duel without trade support", "04:36 · Clean P2 rotation and anchor handoff", "06:48 · Team stacks old hill after spawn flip", "09:05 · Strong three-player break with utility"].map((note, index) => <article key={note}><button aria-label={`Play timestamp ${index + 1}`}><Play size={13}/></button><p><strong>{note.split(" · ")[0]}</strong><span>{note.split(" · ")[1]}</span></p><small>{index % 2 ? "Strength" : "Review"}</small></article>)}
          </div>
        </section>
        <aside className="panel vodForm">
          <div><span className="panelKicker">LOCKED COACH FORM</span><h2>Submit observations</h2><p>These fields become evidence for the weekly AI review.</p></div>
          <label>Overall performance<select disabled={vodLocked} value={rating} onChange={(event) => setRating(event.target.value)}>{[1,2,3,4,5].map((value) => <option key={value} value={value}>{value} / 5</option>)}</select></label>
          <label>Strength<input disabled={vodLocked} defaultValue="Early rotation and hill discipline" /></label>
          <label>Weakness<input disabled={vodLocked} value={weakness} onChange={(event) => setWeakness(event.target.value)} /></label>
          <label>Priority focus<input disabled={vodLocked} value={priority} onChange={(event) => setPriority(event.target.value)} /></label>
          <label>Coach note<textarea disabled={vodLocked} defaultValue="Slow the first contact down. Give Sly enough time to reach the trade lane before challenging." /></label>
          <button className="primaryButton" disabled={vodLocked} onClick={() => { setVodLocked(true); onAction("Manager VOD review submitted and locked"); }}><ClipboardCheck size={15}/>{vodLocked ? "Review submitted" : "Submit & lock review"}</button>
          <button className="textButton" onClick={() => onAction("Player self-report request sent")}>Request player self-report</button>
        </aside>
      </div>}

      {tab === "Strat Board" && <div className="strategyLayout">
        <section className="panel strategyLibrary">
          <div className="viewHeader"><div><span className="panelKicker">TEAM PLAYBOOK</span><h2>Match strategies</h2><p>Versioned plans, roles and discussion in one place.</p></div><button className="primaryButton" onClick={() => onAction("New strategy draft opened")}><Plus size={15}/> New strategy</button></div>
          <div className="stratPicker">{["Summit HP", "Raid Control", "Standoff S&D"].map((name, index) => <button key={name} className={selectedStrat === name ? "active" : ""} onClick={() => setSelectedStrat(name)}><span>{index === 0 ? "HP" : index === 1 ? "CTL" : "S&D"}</span><p><strong>{name}</strong><small>{index === 0 ? "v7 · Match ready" : index === 1 ? "v4 · In review" : "v9 · Match ready"}</small></p><ChevronDown size={14}/></button>)}</div>
        </section>
        <section className="panel strategyBoard">
          <div className="boardTop"><div><span className="panelKicker">{selectedStrat.toUpperCase()} · P2 SETUP</span><h2>Control top and protect weak-side spawn</h2></div><span className="verified"><BadgeCheck size={14}/> Coach approved</span></div>
          <div className="tacticalMap" aria-label="Simplified Summit tactical board"><span className="mapZone zoneOne">P1</span><span className="mapZone zoneTwo">P2</span><span className="mapZone zoneThree">TOP</span><i className="route routeOne"/><i className="route routeTwo"/><b className="playerMarker markerOne">FV</b><b className="playerMarker markerTwo">SL</b><b className="playerMarker markerThree">RG</b><b className="playerMarker markerFour">KG</b></div>
          <div className="roleAssignments">{[["Favour","Hill · Contest late"],["Sly","Entry · Clear top"],["Reign","Anchor · Hold weak"],["Kage","Flex · Watch cut"]].map((role) => <article key={role[0]}><span>{role[0].slice(0,2).toUpperCase()}</span><p><strong>{role[0]}</strong><small>{role[1]}</small></p></article>)}</div>
        </section>
        <aside className="panel strategyThread">
          <div className="panelHeader compact"><div><span className="panelKicker">STRATEGY TALK</span><h2>Team discussion</h2></div><MessageSquare size={17}/></div>
          <div className="threadMessages"><article><span>SL</span><p><strong>Sly <small>18:42</small></strong>Can Reign hold the top cut while I clear control?</p></article><article><span>CO</span><p><strong>Coach Jay <small>18:47</small></strong>Yes—only after Favour confirms the spawn flip.</p></article>{stratNoteAdded && <article><span>FI</span><p><strong>Favour <small>Now</small></strong>Added to the next walkthrough.</p></article>}</div>
          <button className="secondaryButton" onClick={() => {setStratNoteAdded(true); onAction("Strategy note added")}}><Send size={14}/> Add strategy note</button>
          <div className="walkthrough"><CalendarDays size={16}/><p><strong>Next walkthrough</strong><span>Today · 19:30 WAT</span></p><button onClick={() => onAction("Walkthrough reminder set")}>Remind me</button></div>
        </aside>
      </div>}

      {tab === "Training" && <div className="trainingLayout">
        <section className="panel trainingPlan">
          <div className="trainingHeader"><div><span className="livePill"><i/> ADAPTIVE PLAN</span><h2>{player}&apos;s Monday session</h2><p>Built from this week&apos;s verified weaknesses and recent drill history.</p></div><div className="sessionLoad"><span>Session load</span><strong>43 min</strong><small>{completedDrills.length}/3 complete</small></div></div>
          <div className="drillList">{drills.map((drill, index) => { const done = completedDrills.includes(index); return <article className={done ? "done" : ""} key={drill[0]}><button onClick={() => toggleDrill(index)} aria-label={`${done ? "Mark incomplete" : "Complete"} ${drill[0]}`}>{done ? <Check size={16}/> : <Play size={15}/>}</button><span>{String(index + 1).padStart(2,"0")}</span><p><strong>{drill[0]}</strong><small>{drill[1]}</small><em>{drill[2]}</em></p><b>{done ? "Complete" : "Start"}</b></article>})}</div>
          <div className="trainingFooter"><p><RefreshCw size={15}/><span><strong>Anti-repeat is active.</strong> Recently completed drills are excluded from the next plan.</span></p><button className="secondaryButton" onClick={() => {setDrillSet((value) => value === 0 ? 1 : 0); setCompletedDrills([]); onAction("A fresh weakness-based drill set was selected")}}>Rotate drill set</button></div>
        </section>
        <aside className="performanceRail">
          <section className="panel weekPlan"><div className="panelHeader compact"><div><span className="panelKicker">THIS WEEK</span><h2>Training rhythm</h2></div><Dumbbell size={17}/></div>{[["MON","Personal","Active"],["TUE","Team systems","20:00"],["WED","Scrim block","20:00"],["THU","Recovery","Light"],["FRI","Qualifier","19:00"],["SAT","VOD + drills","18:30"],["SUN","Review closes","23:59"]].map((day) => <p key={day[0]}><span>{day[0]}</span><strong>{day[1]}</strong><small>{day[2]}</small></p>)}</section>
          <section className="panel historyCard"><span className="panelKicker">DRILL HISTORY</span><h3>No empty repetition.</h3><p>Opening-duel reset last appeared 12 days ago. Trade-lane work remains because the weakness is still present in current evidence.</p><button className="textButton" onClick={() => onAction("Full training history opened")}>View full history</button></section>
        </aside>
      </div>}
    </div>
  );
}
