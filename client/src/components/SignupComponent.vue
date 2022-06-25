<template>
  <div class="column is-4 is-offset-4">
    <h3 class="title">Créer un compte</h3>
    <div class="box">
      <div class="notification is-danger" v-if="invalidSignup">
        Nom déjà existant
      </div>

      <form v-on:submit.prevent="signup">
        <div class="field control">
          <label class="label" for="name">Nom</label>
          <input type="text" class="input is-large" id="name" placeholder="nom" v-model="name">
        </div>

        <div class="field control">
          <label class="label" for="password">Mot de passe</label>
          <input type="password" class="input is-large" placeholder="mot de passe" v-model="password">
        </div>

        <button class="button is-block is-info is-large is-fullwidth">Créer un compte</button>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SignupComponent',
  data() {
    return {
      name: '',
      password: '',
      invalidSignup: false,
    };
  },
  methods: {
    signup() {
      this.$store.dispatch('signup', { name: this.name, password: this.password })
        .then((_) => {
          this.$router.push('/login');
        })
        .catch((error) => {
          console.log('Error Registering: ', error);
          this.invalidSignup = true;
        });
    },
  },
};
</script>
