<template>
  <section class="hero is-primary is-fullheight">
    <div class="hero-head">
      <nav class="navbar">
        <div class="container">
          <div id="navbarMenuHeroA" class="navbar-menu">
            <div class="navbar-end">
              <router-link to="/" class="navbar-item">Home</router-link>
              <router-link to="/profile" class="navbar-item">Profile</router-link>
              <router-link to="/login" class="navbar-item">Login</router-link>
              <router-link to="/signup" class="navbar-item">Signup</router-link>
              <router-link to="/logout" class="navbar-item">Logout</router-link>
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
