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
              <router-link v-if="!isAuthenticated" to="/login" class="navbar-item">
                Login
              </router-link>
              <router-link v-if="!isAuthenticated" to="/signup" class="navbar-item">
                Signup
              </router-link>
              <router-link v-if="isAuthenticated" to="/logout" class="navbar-item">
                Logout
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
  },
};
</script>
