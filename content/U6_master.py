import runpy, os

def pick(fn, idx):
    L0 = runpy.run_path(os.path.join('content', fn), init_globals={'S': S})['L']
    return [L0['scenes'][i - 1] for i in idx]

intro = [
 S('Namaste! Yeh hai Master Class, poora Software Engineering ek hi video mein. Rule simple hai: jo common sense hai uske liye bas ek line. Jo sach mein mushkil hai, jaise agile versus traditional, models, testing numericals, COCOMO, uska detail. Aur sab topics ko ek story se jodenge, taaki yaad rakhna aasaan ho. Pehle poora map dekh lo.',
  'Master Class: ek line basics, detail mein hard cheezein, sab linked',
  [['map', 'SOFTWARE ENGINEERING MASTER CLASS', [('1 Intro + Agile', ['Structured vs OOAD', 'Agile vs Traditional', 'Scrum', 'FDD domain model']), ('2 Requirements', ['Types', 'Elicitation', 'Use case', 'SRS', 'ER, DFD, State']), ('3 Design + Models', ['Coupling cohesion', 'Architecture styles', 'Waterfall, Prototype', 'Incremental, V, Spiral, RAD']), ('4 Testing', ['V and V', 'Levels, integration', 'White box, CC numerical', 'BVA, ECP, decision table']), ('5 PM + Quality', ['COCOMO, FP', 'CPM, EVM', 'Risk', 'McCall, CMM', 'Reliability']), ('One liners', ['Crisis', 'SDLC', 'RE steps', 'SCM', 'Maintenance'])]]],
  [], 'Master Class Map', True, False),
 S('Pehle woh topics jo common sense hain. Inke liye ek ek line yaad kar lo aur answer mein keywords daal do. Software crisis: late, costly, buggy. SDLC: requirement, design, code, test, maintain. Agile: chhote iterations, change welcome. XP: pair programming aur TDD. Crystal: team size ke hisaab se. DevOps: dev aur ops ek saath. SCM: baseline aur change control. Maintenance: corrective, adaptive, perfective, preventive. ISO nine thousand one: quality management standard.',
  'Common sense topics: ek line kaafi',
  [['tbl', [['Topic', 'One line'], ['Software crisis', 'Late + over budget + buggy (cost, time, quality)'], ['SDLC', 'Req > Design > Code > Test > Maintain'], ['Agile', 'Small iterations, change welcome'], ['XP', 'Pair programming, TDD, small releases'], ['Crystal / DevOps', 'By team size / Dev + Ops with CI CD'], ['RE steps', 'Inception, elicit, analyse, specify, validate, manage'], ['SCM', 'Baseline + change control'], ['Maintenance', 'Corrective, adaptive, perfective, preventive'], ['Design patterns', 'Proven reusable solutions']]]],
  ['## Rule', 'Basics: one line + keywords', 'Hard topics: diagram + table + steps', '! Keywords to sprinkle: cost, time, quality, risk, requirements'], None, False, False),
 S('Ab sab topics ko ek story se jodte hain. Maan lo Library Management System bana rahe ho. Pehle requirements: use case aur SRS. Phir design: ER, DFD, coupling cohesion. Phir model chuno, agile ya waterfall. Phir code aur test, BVA aur cyclomatic. Phir estimate, COCOMO aur critical path. Phir quality, McCall aur CMM. Aakhir mein maintenance. Har answer mein bas yeh batao ki yeh topic is chain mein kahan aata hai.',
  'Ek story: Library System, requirement se maintenance tak',
  [['graph', [('a', 'Requirements: use case, SRS', 0.12, 0.1, 'box', 0), ('b', 'Design: ER, DFD, coupling', 0.5, 0.1, 'box', 1), ('c', 'Model: agile / waterfall', 0.88, 0.1, 'box', 2), ('d', 'Test: BVA, CC, decision table', 0.88, 0.5, 'box', 3), ('e', 'Estimate: COCOMO, CPM', 0.5, 0.5, 'box', 4), ('f', 'Quality: McCall, CMM', 0.12, 0.5, 'box', 5), ('g', 'Maintain', 0.5, 0.9, 'oval', 0)], [('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e'), ('e', 'f'), ('f', 'g')], 330]],
  ['## How to link in an answer', 'Say where the topic sits in the SDLC chain', 'Use one running example (Library system)', '! Example: use case gives test cases, SRS gives estimation size', '~ Linked topics are remembered faster'], None, False, False),
]

basics_tail = [
 S('Ab mnemonics ka cheat sheet. Plan versus Adapt: traditional ya agile. Stub neeche wala, driver upar wala. McCall: C R U I E, M F T, P R I. CMM: I Really Do Miss Ordering. Model kaun sa: Clear waterfall, Unclear prototype, Risk spiral, Test V, Fast RAD, Changing agile. BVA: min, min plus, nominal, max minus, max. Cyclomatic: E minus N plus two. COCOMO: a KLOC power b. Yeh table photo kheench lo.',
  'Mnemonics: yaad karo aur photo kheencho',
  [['tbl', [['Topic', 'Trick'], ['Traditional vs Agile', 'PLAN vs ADAPT'], ['Integration', 'Stub = down, Driver = up'], ['McCall', 'CRUIE - MFT - PRI'], ['CMM', 'I Really Do Miss Ordering'], ['Model choice', 'Clear-W, Unclear-P, Risk-S, Test-V, Fast-RAD'], ['BVA', 'min, min+, nom, max-, max'], ['Coupling', 'Content worst, Data best'], ['Cohesion', 'Functional best, Coincidental worst'], ['V and V', 'Right way vs right thing']]]],
  [], 'Mnemonic Cheat Sheet', True, False),
 S('Last mein formula sheet. Cyclomatic: E minus N plus two, ya P plus ek. BVA: four n plus one, robust six n plus one, worst five power n. COCOMO: E barabar a KLOC power b, into EAF. Time barabar c E power d. Function point: UFP into point sixty five plus point zero one sigma Fi. Earned value: SV barabar EV minus PV, CV barabar EV minus AC. Risk exposure barabar P into loss. MTBF barabar MTTF plus MTTR. Availability barabar MTTF divide MTBF. Bas, ab tum ready ho!',
  'Formula sheet: sab numericals ek jagah',
  [['tbl', [['Topic', 'Formula'], ['Cyclomatic', 'V(G) = E - N + 2 = P + 1'], ['BVA', '4n+1, robust 6n+1, worst 5^n'], ['COCOMO', 'E = a KLOC^b x EAF, D = c E^d'], ['Function point', 'FP = UFP x (0.65 + 0.01 sum Fi)'], ['Earned value', 'SV = EV-PV, CV = EV-AC'], ['Risk exposure', 'RE = P x Loss'], ['Reliability', 'MTBF = MTTF+MTTR, Avail = MTTF/MTBF'], ['Critical path', 'Longest path, zero float']]]],
  [], 'Formula Sheet', True, False),
]

scenes = (intro + pick('U1_intro.py', [5, 7, 8, 10]) + pick('U2_requirements.py', [3, 4, 5, 6, 9, 10, 11])
  + pick('U3_design_models.py', [2, 5, 7, 8, 9, 10, 11, 12, 13]) + pick('U4_testing.py', [2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14])
  + pick('U5_pm_quality.py', [2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 14]) + basics_tail)
L = dict(title='Master Class: All 5 Units', points=[
 'Plan vs Adapt: traditional is plan driven, agile adapts to change',
 'Stub is the called module in top down, driver is the caller in bottom up',
 'Cyclomatic V of G = E minus N plus 2 = number of independent paths',
 'BVA gives 4n plus 1 cases, robust 6n plus 1, worst case 5 to the power n',
 'COCOMO effort = a KLOC to the b times EAF, time = c effort to the d',
 'McCall: CRUIE, MFT, PRI. CMM: Initial, Repeatable, Defined, Managed, Optimizing',
 'Choose model: clear waterfall, unclear prototype, risk spiral, test V, fast RAD, changing agile',
 'Low coupling and high cohesion is good design',
 'Verification is building it right, validation is building the right thing',
 'Link every topic to the SDLC chain and write definition, diagram, points, example, table, conclusion'], scenes=scenes)
