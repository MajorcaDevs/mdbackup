(() => {
  const betaRegex = /^v?\d+\.\d+\.\d+-.+$/

  // Adapted from https://raw.githubusercontent.com/containous/structor/master/traefik-menu.js.gotmpl
  const addMaterialMenu = (elt, versions) => {
    const current = versions.find(value => value.title === window.app.version)

    // menu item (the whole container)
    const rootLi = document.createElement('li')
    rootLi.classList.add('md-nav__item')
    rootLi.classList.add('md-nav__item--nested')

    // the "button" that triggers the menu change
    const input = document.createElement('input')
    input.classList.add('md-toggle')
    input.classList.add('md-nav__toggle')
    input.setAttribute('data-md-toggle', 'nav-10000000')
    input.id = 'nav-10000000'
    input.type = 'checkbox'

    rootLi.appendChild(input)

    // the "label"/text of the menu item
    const lbl01 = document.createElement('label')
    lbl01.classList.add('md-nav__link')
    lbl01.setAttribute('for', 'nav-10000000')
    lbl01.textContent = current.title + ' '

    rootLi.appendChild(lbl01)

    // the icon in the menu item that says "hey there's more if you click here"
    const icon01 = document.createElement('span')
    icon01.classList.add('md-nav__icon')
    icon01.classList.add('md-icon')
    icon01.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M8.59 16.58L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.42z"></path></svg>'

    lbl01.appendChild(icon01)

    // the contents of the new menu
    const nav = document.createElement('nav')
    nav.classList.add('md-nav')
    nav.setAttribute('aria-label', current.title)
    nav.setAttribute('data-md-level','1')

    rootLi.appendChild(nav)

    // the menu header
    const lbl02 = document.createElement('label')
    lbl02.classList.add('md-nav__title')
    lbl02.setAttribute('for', 'nav-10000000')
    lbl02.textContent = current.title + ' '

    nav.appendChild(lbl02)

    // the icon in the menu item header to go back
    const icon02 = document.createElement('span')
    icon02.classList.add('md-nav__icon')
    icon02.classList.add('md-icon')
    icon02.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20 11v2H8l5.5 5.5-1.42 1.42L4.16 12l7.92-7.92L13.5 5.5 8 11h12z"></path></svg>'

    lbl02.appendChild(icon02)

    const ul = document.createElement('ul')
    ul.classList.add('md-nav__list')
    ul.setAttribute('data-md-scrollfix','')

    nav.appendChild(ul)

    for (let i = 0; i < versions.length; i++) {
      const li = document.createElement('li')
      li.classList.add('md-nav__item')

      ul.appendChild(li)

      const a = document.createElement('a')
      a.classList.add('md-nav__link')
      if (versions[i].selected) {
        a.classList.add('md-nav__link--active')
      }

      let url = window.app.homepage || '/'
      if (versions[i].path) {
        url = versions[i].path + '/'
      }
      a.href = url
      a.title = versions[i].title
      a.text = versions[i].title

      li.appendChild(a)
    }

    elt.appendChild(rootLi)
  }

  // United theme

  const addMenu = (elt, versions) => {
    const li = document.createElement('li')
    li.classList.add('md-nav__item')
    li.style.cssText = 'padding-top: 1em;'

    const select = document.createElement('select');
    select.classList.add('md-nav__link');
    select.style.cssText = 'background: white;border: none;color: #00BCD4;-webkit-border-radius: 5px;-moz-border-radius: 5px;border-radius: 5px;overflow: hidden;padding: 0.1em;'
    select.setAttribute('onchange', 'location = this.options[this.selectedIndex].value;')

    for (let i = 0; i < versions.length; i++) {
      let opt = document.createElement('option')
      opt.value = window.app.homepage || '/'
      if (versions[i].path) {
          opt.value = versions[i].path + '/'
      }
      opt.text = versions[i].text
      opt.selected = versions[i].selected
      select.appendChild(opt)
    }

    li.appendChild(select)
    elt.appendChild(li)
  }


  const unitedSelector = 'div.navbar.navbar-default.navbar-fixed-top div.container div.navbar-collapse.collapse ul.nav.navbar-nav.navbar-right'
  const materialSelector = 'div.md-container main.md-main div.md-main__inner.md-grid div.md-sidebar.md-sidebar--primary div.md-sidebar__scrollwrap div.md-sidebar__inner nav.md-nav.md-nav--primary ul.md-nav__list'

  fetch(window.app.homepage + '/versions.json')
    .then(res => res.json())
    .then(versions => {
      let elt = document.querySelector(materialSelector)
      if (elt) {
          addMaterialMenu(elt, versions)
      } else {
          elt = document.querySelector(unitedSelector)
          addMenu(elt, versions)
      }
    })
    .catch(err => console.error(err))
})()
