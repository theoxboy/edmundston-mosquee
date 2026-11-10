#!/bin/sh
# Rejoue tout le portage CCIE v2 depuis l'état commité. $1 = scratchpad (bundle + scripts), $2 = repo, $3 = planches décodées
S=$1; R=$2; V=$3; cd "$R" || exit 1
ls *.dc.html 404.html index.html site-gratuit-mosquee.html | grep -v -E '^(SA-|TH-)' | while read p; do python3 -I $S/port_v2.py $S $V/1__CCIE_Horaires_PC.html "$R/$p" >/dev/null || echo "FAIL $p"; done
python3 -I $S/port_home.py $S Main.dc.html index.html M-Accueil.dc.html T-Accueil.dc.html >/dev/null || echo FAIL home
set -- TH-Ramadan-Accueil 4__CCIE_Ramadan_Accueil_PC TH-Ramadan-Page 4__CCIE_Ramadan_Page_d_di_e_PC TH-Fitr-Accueil 4__CCIE_A_d_al_Fitr_Accueil_PC TH-Fitr-Page 4__CCIE_A_d_al_Fitr_Page_d_di_e_PC TH-Adha-Accueil 4__CCIE_A_d_al_Adha_Accueil_PC TH-Adha-Page 4__CCIE_A_d_al_Adha_Page_d_di_e_PC TH-Vendredi-Accueil 4__CCIE_Vendredi_Accueil_PC TH-Vendredi-Horaires 4__CCIE_Vendredi_Horaires_PC TH-Vendredi-Khutba 4__CCIE_Vendredi_Khutba_PC
while [ $# -gt 0 ]; do python3 -I $S/port_th.py $S "$R/$1.dc.html" "$V/$2.html" >/dev/null || echo "FAIL $1"; shift 2; done
set -- SA-Connexion.dc.html Connexion_PC superadmin.html Connexion_PC SA-Panneau.dc.html Panneau_PC SA-Site.dc.html Superadmin_Site_entier SA-Horaires.dc.html Superadmin_Horaires SA-APropos.dc.html Superadmin_propos SA-Services.dc.html Superadmin_Services SA-Dons.dc.html Superadmin_Faire_un_don SA-Evenements.dc.html Superadmin_v_nements SA-Ressources.dc.html Superadmin_Ressources SA-Contact.dc.html Superadmin_Contact SA-Pages.dc.html Superadmin_Cr_er_une_page SA-PageEditeur.dc.html Superadmin_diteur_de_page SA-Formulaires.dc.html Superadmin_Horaires SA-Traductions.dc.html Superadmin_Horaires
while [ $# -gt 0 ]; do python3 -I $S/port_sa.py $S "$V/3__$2.html" "$1" >/dev/null || echo "FAIL $1"; shift 2; done
# --- deuxième lot : textes, logo, thèmes, menu mobile, SA-Comptes, en-tête ---
python3 -I $S/fix_textes.py $S "$R" >/dev/null || echo FAIL textes
grep -l '__bundler/template' *.html | xargs python3 -I $S/port_logo.py $S $V/1__CCIE_Horaires_PC.html >/dev/null || echo FAIL logo
set -- TH-Ramadan-Accueil Ramadan_Accueil_PC TH-Ramadan-Page Ramadan_Page_d_di_e_PC TH-Fitr-Accueil A_d_al_Fitr_Accueil_PC TH-Fitr-Page A_d_al_Fitr_Page_d_di_e_PC TH-Adha-Accueil A_d_al_Adha_Accueil_PC TH-Adha-Page A_d_al_Adha_Page_d_di_e_PC TH-Vendredi-Accueil Vendredi_Accueil_PC TH-Vendredi-Horaires Vendredi_Horaires_PC TH-Vendredi-Khutba Vendredi_Khutba_PC
while [ $# -gt 0 ]; do python3 -I $S/port_thx.py $S "$V/4__CCIE_$2.html" "$1.dc.html" >/dev/null || echo "FAIL thx $1"; shift 2; done
grep -l '__bundler/template' *.html | xargs python3 -I $S/port_mm.py $S >/dev/null || echo FAIL menu
python3 -I $S/port_comptes.py $S $V/3__Panneau_PC.html SA-Comptes.html >/dev/null || echo FAIL comptes
python3 -I $S/port_comptes_logo.py $S $V/1__CCIE_Horaires_PC.html SA-Comptes.html >/dev/null || echo FAIL comptes-logo
grep -l '__bundler/template' *.html | grep -v -E '^(SA-|TH-|superadmin)' | xargs python3 -I $S/port_brand.py $S >/dev/null || echo FAIL marque
python3 -I $S/port_hero.py $S Main.dc.html index.html M-Accueil.dc.html T-Accueil.dc.html >/dev/null || echo FAIL hero
