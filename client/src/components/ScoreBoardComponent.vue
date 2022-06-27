<template>
  <div class="columns">
    <div class="column is-2">
      <GroupNavbar />
    </div>
    <div class="column">
      <h3 class="title">Classement</h3>
      <div class="box">
        <div class="table-container">
          <table class="table is-fullwidth is-striped">
            <thead>
              <tr>
                <th>Joueur</th>
                <th>Nombre de matchs trouvés</th>
                <th>Nombre de scores trouvés</th>
                <th>Points</th>
              </tr>
            </thead>
            <tr v-for="res in scoreBoardResource">
              <td>{{ res["name"] }}</td>
              <td>{{ res["number_match_guess"] }}</td>
              <td>{{ res["number_score_guess"] }}</td>
              <td>{{ res["points"] }}</td>
            </tr>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import GroupNavbar from './GroupNavbar.vue';

export default {
  name: 'ScoreBoardComponent',
  components: {
    GroupNavbar,
  },
  data() {
    return {
      scoreBoardResource: [],
    };
  },
  methods: {
    getScoreBoard() {
      this.$store.dispatch('getScoreBoard')
        .then((res) => { this.scoreBoardResource = res.data.result; });
    },
  },
  beforeEnter(to, from, next) {
    if (!this.$store.getters.isAuthenticated) {
      this.$store.dispatch('logout');
      next('/login');
    } else {
      next();
    }
  },
  created() {
    this.getScoreBoard();
  },
};

</script>
