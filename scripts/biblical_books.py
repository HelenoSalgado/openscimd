# Lista exaustiva de livros bíblicos e todas as suas possíveis abreviações e grafias em português (com e sem acento, com numerais cardinais e romanos, e sem espaçamento)

BIBLE_BOOKS = [
    # Pentateuco
    r"Gênesis", r"Genesis", r"Gn", r"Gên", r"Gen",
    r"Êxodo", r"Exodo", r"Ex", r"Êxo", r"Exo",
    r"Levítico", r"Levitico", r"Lv", r"Lev",
    r"Números", r"Numeros", r"Nm", r"Núm", r"Num",
    r"Deuteronômio", r"Deuteronomio", r"Dt", r"Deut", r"Deu",
    
    # Históricos
    r"Josué", r"Josue", r"Js", r"Jos",
    r"Juízes", r"Juizes", r"Jz", r"Juí", r"Jui",
    r"Rute", r"Rt", r"Rut",
    
    r"1\s*Samuel", r"I\s*Samuel", r"1º\s*Samuel", r"1ª\s*Samuel", r"1\s*Sm", r"I\s*Sm", r"1\s*Sam", r"I\s*Sam",
    r"2\s*Samuel", r"II\s*Samuel", r"2º\s*Samuel", r"2ª\s*Samuel", r"2\s*Sm", r"II\s*Sm", r"2\s*Sam", r"II\s*Sam",
    
    r"1\s*Reis", r"I\s*Reis", r"1º\s*Reis", r"1ª\s*Reis", r"1\s*Rs", r"I\s*Rs",
    r"2\s*Reis", r"II\s*Reis", r"2º\s*Reis", r"2ª\s*Reis", r"2\s*Rs", r"II\s*Rs",
    
    r"1\s*Crônicas", r"1\s*Cronicas", r"I\s*Crônicas", r"I\s*Cronicas", r"1º\s*Crônicas", r"1\s*Cr", r"I\s*Cr", r"1\s*Crôn", r"1\s*Cron",
    r"2\s*Crônicas", r"2\s*Cronicas", r"II\s*Crônicas", r"II\s*Cronicas", r"2º\s*Crônicas", r"2\s*Cr", r"II\s*Cr", r"2\s*Crôn", r"2\s*Cron",
    
    r"Esdras", r"Ed", r"Esd",
    r"Neemias", r"Ne", r"Neem", r"Nee",
    r"Ester", r"Et", r"Est",
    
    # Poéticos
    r"Jó", r"Jo", # (cuidado com Jo/João, mas na regex pega ambos)
    r"Salmos", r"Salmo", r"Sl", r"Sal", r"Salm",
    r"Provérbios", r"Proverbios", r"Pv", r"Prov", r"Pr",
    r"Eclesiastes", r"Ec", r"Ecl",
    r"Cânticos", r"Canticos", r"Cântico dos Cânticos", r"Cantares", r"Ct", r"Cânt", r"Cant",
    
    # Profetas Maiores
    r"Isaías", r"Isaias", r"Is", r"Isa",
    r"Jeremias", r"Jr", r"Jer",
    r"Lamentações", r"Lamentacoes", r"Lm", r"Lam",
    r"Ezequiel", r"Ez", r"Eze", r"Ezeq",
    r"Daniel", r"Dn", r"Dan",
    
    # Profetas Menores
    r"Oseias", r"Oséias", r"Os", r"Ose", r"Osé",
    r"Joel", r"Jl", r"Joe",
    r"Amós", r"Amos", r"Am", r"Amó", r"Amo",
    r"Obadias", r"Ob", r"Oba",
    r"Jonas", r"Jn", r"Jon",
    r"Miqueias", r"Miquéias", r"Mq", r"Miq",
    r"Naum", r"Na", r"Nau",
    r"Habacuque", r"Hc", r"Hab",
    r"Sofonias", r"Sf", r"Sof",
    r"Ageu", r"Ag", r"Age",
    r"Zacarias", r"Zc", r"Zac",
    r"Malaquias", r"Ml", r"Mal",
    
    # Evangelhos
    r"Mateus", r"Mt", r"Mat",
    r"Marcos", r"Mc", r"Mar", r"Marc",
    r"Lucas", r"Lc", r"Luc",
    r"João", r"Joao", r"Jo", r"Joã",
    r"Atos", r"At", r"Ato", r"Atos dos Apóstolos",
    
    # Epístolas Paulinas
    r"Romanos", r"Rm", r"Rom",
    r"1\s*Coríntios", r"1\s*Corintios", r"I\s*Coríntios", r"1º\s*Coríntios", r"1\s*Co", r"I\s*Co", r"1\s*Cor", r"I\s*Cor",
    r"2\s*Coríntios", r"2\s*Corintios", r"II\s*Coríntios", r"2º\s*Coríntios", r"2\s*Co", r"II\s*Co", r"2\s*Cor", r"II\s*Cor",
    r"Gálatas", r"Galatas", r"Gl", r"Gál", r"Gal",
    r"Efésios", r"Efesios", r"Ef", r"Efé", r"Efe",
    r"Filipenses", r"Fp", r"Fil", r"Flp",
    r"Colossenses", r"Cl", r"Col",
    
    r"1\s*Tessalonicenses", r"I\s*Tessalonicenses", r"1º\s*Tessalonicenses", r"1\s*Ts", r"I\s*Ts", r"1\s*Tes", r"I\s*Tes",
    r"2\s*Tessalonicenses", r"II\s*Tessalonicenses", r"2º\s*Tessalonicenses", r"2\s*Ts", r"II\s*Ts", r"2\s*Tes", r"II\s*Tes",
    
    r"1\s*Timóteo", r"1\s*Timoteo", r"I\s*Timóteo", r"1º\s*Timóteo", r"1\s*Tm", r"I\s*Tm", r"1\s*Tim", r"I\s*Tim",
    r"2\s*Timóteo", r"2\s*Timoteo", r"II\s*Timóteo", r"2º\s*Timóteo", r"2\s*Tm", r"II\s*Tm", r"2\s*Tim", r"II\s*Tim",
    
    r"Tito", r"Tt", r"Tit",
    r"Filemom", r"Filemon", r"Fm", r"Flm", r"Filêm", r"Filem",
    
    # Epístolas Gerais e Apocalipse
    r"Hebreus", r"Hb", r"Heb",
    r"Tiago", r"Tg", r"Tia", r"Tgo",
    
    r"1\s*Pedro", r"I\s*Pedro", r"1º\s*Pedro", r"1\s*Pe", r"I\s*Pe", r"1\s*Ped", r"I\s*Ped",
    r"2\s*Pedro", r"II\s*Pedro", r"2º\s*Pedro", r"2\s*Pe", r"II\s*Pe", r"2\s*Ped", r"II\s*Ped",
    
    r"1\s*João", r"1\s*Joao", r"I\s*João", r"1º\s*João", r"1\s*Jo", r"I\s*Jo", r"1\s*Joã",
    r"2\s*João", r"2\s*Joao", r"II\s*João", r"2º\s*João", r"2\s*Jo", r"II\s*Jo", r"2\s*Joã",
    r"3\s*João", r"3\s*Joao", r"III\s*João", r"3º\s*João", r"3\s*Jo", r"III\s*Jo", r"3\s*Joã",
    
    r"Judas", r"Jd", r"Jud",
    r"Apocalipse", r"Ap", r"Apo", r"Apoc"
]
