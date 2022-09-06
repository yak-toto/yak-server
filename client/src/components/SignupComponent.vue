<template>
  <div class="column is-4 is-offset-4">
    <h3 class="title">Créer un compte</h3>
    <div class="box">
      <div class="notification is-danger" v-if="invalidSignup">
        Nom déjà existant
      </div>

      <form v-on:submit.prevent="signup">
        <div class="field control">
          <label class="label" for="pseudo">
            Pseudo
            <input type="text" class="input is-large" id="pseudo" placeholder="pseudo" v-model="name">
          </label>
        </div>

        <div class="field control">
          <label class="label" for="firstName">
            Prénom
            <input type="text" class="input is-large" id="firstName" placeholder="prénom" v-model="firstName">
          </label>
        </div>

        <div class="field control">
          <label class="label" for="lastName">
            Nom de famille
            <input type="text" class="input is-large" id="lastName" placeholder="nom de famille" v-model="lastName">
          </label>
        </div>

        <div class="field control">
          <label class="label" for="password">
            Mot de passe
            <input type="password" class="input is-large"
              placeholder="mot de passe" v-model="password">
          </label>
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
      firstName: '',
      lastName: '',
      password: '',
      invalidSignup: false,
    };
  },
  methods: {
    signup() {
      this.$store.dispatch('signup', { name: this.name, first_name: this.firstName, last_name: this.lastName, password: this.password })
        .then(() => {
          this.$router.push('/login');
        })
        .catch(() => {
          this.invalidSignup = true;
        });
    },
  },
};
</script>
