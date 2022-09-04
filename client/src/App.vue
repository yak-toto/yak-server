<template>
  <section class="hero is-primary is-fullheight">
    <div class="hero-head">
      <nav class="navbar">
        <div class="container">
          <div id="navbarMenuHeroA" class="navbar-menu is-active">
            <div class="navbar-start">
              <div v-if="
                $store.getters.isAuthenticated &&
                $route.name !== 'login' && $route.name !== 'signup'"
                class="has-text-white navbar-item"
              >
                Utilisateur:&nbsp;<strong>{{ $store.getters.getUserName }}</strong>
              </div>
              <a @click="computePoints"
                v-if="
                  $store.getters.isAuthenticated &&
                  $route.name !== 'login' && $route.name !== 'signup' &&
                  $store.getters.getUserName === 'admin'"
                class="navbar-item"
              >
                Calculer les points
              </a>
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

<script>
export default {
  name: 'GroupComponent',
  methods: {
    computePoints() {
      this.$store.dispatch('computePoints');
    }
  },
};
</script>
