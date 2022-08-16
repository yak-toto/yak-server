<template>
  <section class="hero is-primary is-fullheight">
    <div class="hero-head">
      <nav class="navbar">
        <div class="container">
          <div id="navbarMenuHeroA" class="navbar-menu is-active">
            <div class="navbar-start">
              <div v-if="$store.getters.isAuthenticated" class="has-text-white navbar-item">
                Utilisateur:&nbsp;<strong>{{ $store.getters.getUserName }}</strong>
              </div>
            </div>
            <div class="navbar-end">
              <router-link
                  to="/login" class="navbar-item"
                  v-if="!($store.getters.isAuthenticated) && !($route.name === 'login')">
                Se connecter
              </router-link>
              <router-link
                  to="/signup" class="navbar-item"
                  v-if="!($store.getters.isAuthenticated) && !($route.name == 'signup')">
                Créer un compte
              </router-link>
              <router-link
                  to="/logout" class="navbar-item"
                  v-if="($store.getters.isAuthenticated)">
                Se déconnecter
              </router-link>
            </div>
          </div>
        </div>
      </nav>
    </div>

    <div class="hero-body">
      <div class="container has-text-centered">
        <router-view/>
      </div>
    </div>
  </section>
</template>
