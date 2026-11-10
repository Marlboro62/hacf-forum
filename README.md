# Forum HACF pour Home Assistant

<p>
  ☕ <strong>Si cette carte vous est utile, vous pouvez soutenir le projet :</strong>
</p>

<div style="white-space: nowrap; line-height: 0;">
  <a
    href="https://www.buymeacoffee.com/Marlboro62"
    target="_blank"
    rel="noopener noreferrer"
    style="display: inline-block; text-decoration: none; vertical-align: middle;"
  ><img
    src="https://img.buymeacoffee.com/button-api/?text=Offrir%20un%20caf%C3%A9&emoji=%E2%98%95&slug=Marlboro62&button_colour=FF5F5F&font_colour=ffffff&font_family=Cookie&outline_colour=000000&coffee_colour=FFDD00"
    alt="Offrir un café sur Buy Me a Coffee"
    height="45"
    style="display: block; border: 0;"
  ></a>&nbsp;&nbsp;<a
    href="https://ko-fi.com/M4M2QL45X"
    target="_blank"
    rel="noopener noreferrer"
    style="display: inline-block; text-decoration: none; vertical-align: middle;"
  ><img
    src="https://storage.ko-fi.com/cdn/kofi6.png?v=6"
    alt="Soutenir le projet sur Ko-fi"
    height="45"
    style="display: block; border: 0;"
  ></a>
</div>

Intégration et carte **non officielles** pour suivre le [forum HACF](https://forum.hacf.fr) (communauté francophone de Home Assistant) depuis votre tableau de bord : **derniers sujets**, **vos sujets** et **vos notifications**.

> Ce projet n'est pas affilié à HACF. Il lit les pages publiques du forum et, si vous le choisissez, vos notifications avec un accès en lecture seule que vous pouvez retirer à tout moment.

## Fonctionnalités

- **Derniers sujets** : tout le forum ou une catégorie au choix, avec la catégorie, les réponses, les vues, les « j'aime », l'heure et l'auteur du dernier message. Les sujets actifs depuis votre dernière visite sont marqués **nouveau**.
- **Mes sujets** : les sujets ouverts par votre pseudo, avec le nombre de **nouvelles réponses** (+3) depuis votre dernière visite.
- **Notifications** (compte relié, facultatif) : mentions, réponses, citations, « j'aime », messages privés, badges… Les non lues sont mises en avant, leur nombre s'affiche sur l'onglet.
- Un clic sur une ligne ouvre le sujet ou le message sur le forum, dans un nouvel onglet.
- **La carte s'installe avec l'intégration** : aucune ressource à ajouter dans les tableaux de bord.
- Interface en **français**, **anglais** et **polonais** (langue de Home Assistant).
- Couleurs : bleu nuit (style des cartes MyElectricalData), version claire automatique, ou thème de Home Assistant.

## Installation

### Avec HACS

1. Dans **Paramètres › Marketplace** (ou HACS avant Home Assistant 2026.11), menu **⋮** → **Dépôts personnalisés** : adresse `https://github.com/Marlboro62/hacf-forum`, type **Intégration**.
2. Cherchez **HACF Forum**, téléchargez-la, puis **redémarrez Home Assistant**.

### Ajouter l'intégration

1. **Paramètres › Appareils et services › Ajouter une intégration › HACF Forum**.
2. **Pseudo sur le forum HACF** : facultatif, pour l'onglet « Mes sujets ».
3. Choisissez **Relier mon compte HACF** pour les notifications, ou **Terminer** (c'est possible plus tard dans les options).

### Relier votre compte (notifications, facultatif)

1. Connectez-vous au forum HACF dans votre navigateur.
2. Dans Home Assistant, ouvrez le lien **« cette page d'autorisation »** affiché par l'intégration.
3. Sur le forum, cliquez sur **Autoriser** : un long texte s'affiche.
4. Copiez **tout** ce texte et collez-le dans Home Assistant.

L'accès est **en lecture seule** (sujets et notifications) : l'intégration ne peut ni écrire, ni répondre, ni modifier votre compte. Le texte affiché par le forum est chiffré pour votre Home Assistant seulement. Pour retirer l'accès : profil du forum › **Préférences › Sécurité › Applications**, et dans Home Assistant **Configurer › Délier mon compte HACF**.

## La carte

```yaml
type: custom:hacf-forum-card
```

Elle trouve seule les capteurs de l'intégration. Elle est aussi proposée dans la liste des cartes (**Forum HACF**), avec un éditeur visuel.

| Option | Rôle | Défaut |
| --- | --- | --- |
| `title` | Titre | `Forum HACF` |
| `show_latest`, `show_mine`, `show_notifications` | Onglets affichés | `true` |
| `max_items` | Nombre de lignes par onglet | `10` |
| `show_avatars` | Avatar de l'auteur du dernier message | `true` |
| `theme` | `v2` (bleu nuit), `auto` (clair si Home Assistant est en mode clair) ou `ha` (thème de Home Assistant) | `v2` |
| `language` | `auto`, `fr`, `en` ou `pl` | `auto` |

Le bouton **Tout marquer comme vu** remet à zéro les « nouveau » et « +N » de l'onglet affiché (mémorisés dans le navigateur).

## Options de l'intégration

**Paramètres › Appareils et services › HACF Forum › Configurer** :

- **Catégorie suivie** pour les derniers sujets (« — » : tout le forum) ;
- **Nombre de sujets** gardés (5 à 50, 20 par défaut) ;
- **Fréquence de mise à jour** (10 minutes par défaut, 5 au minimum pour ménager le forum) ;
- **Relier** ou **délier** votre compte.

## Capteurs

| Capteur | État | Attributs |
| --- | --- | --- |
| Derniers sujets | Sujets actifs ces dernières 24 heures | `topics`, `category`, `forum_url` |
| Mes sujets | Nombre de vos sujets | `topics`, `username`, `forum_url` |
| Notifications | Notifications non lues | `notifications`, `account`, `forum_url` |

Les listes (`topics`, `notifications`) ne sont pas enregistrées dans l'historique de Home Assistant. Le capteur **Notifications** peut servir à une automatisation (par exemple, une notification sur le téléphone quand il augmente).

## Vie privée

- Seul votre Home Assistant contacte `forum.hacf.fr`, toutes les 10 minutes par défaut.
- La clé du compte reste dans Home Assistant ; elle est retirée des **diagnostics**, comme votre pseudo.
- Les avatars sont chargés depuis le forum par votre navigateur.

## Signaler un problème

Ouvrez une [issue GitHub](https://github.com/Marlboro62/hacf-forum/issues), avec les **diagnostics** de l'intégration (téléchargeables depuis sa page). Ne collez jamais le texte affiché par le forum lors de l'autorisation.

## Licence

MIT. Le nom HACF désigne le forum suivi ; ce projet n'est ni produit ni validé par HACF.
