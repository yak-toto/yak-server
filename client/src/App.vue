<template>
  <section class="hero is-primary is-fullheight">
    <div class="hero-head">
      <nav class="navbar">
        <div class="container">
          <div id="navbarMenuHeroA" class="navbar-menu">
            <div class="navbar-start">
              <div v-if="res = getUserName" class="has-text-white navbar-item">
                Utilisateur:&nbsp;<strong>{{ res }}</strong>
              </div>
            </div>
            <div class="navbar-end">
              <router-link v-if="!isAuthenticated && !isCurrentRouteLogin" to="/login" class="navbar-item">
                Se connecter
              </router-link>
              <router-link v-if="!isAuthenticated && !isCurrentRouteSignup" to="/signup" class="navbar-item">
                Créer un compte
              </router-link>
              <router-link v-if="isAuthenticated" to="/logout" class="navbar-item">
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
  computed: {
    isAuthenticated() {
      return this.$store.getters.isAuthenticated;
    },
    getUserName() {
      return this.$store.getters.getUserName;
    },
    isCurrentRouteLogin() {
      return this.$route.name == 'login';
    },
    isCurrentRouteSignup() {
      return this.$route.name == 'signup';
    },
  },
};
</script>
