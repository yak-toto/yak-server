<template>
  <div>
    <nav class="navbar">
      <div class="container">
        <div id="navbarMenu" class="navbar-menu">
          <div class="navbar">
            <GroupButton v-for="group_name in groups_names" :group_name="group_name"></GroupButton>
            <ScoreBoardButton />
          </div>
        </div>
      </div>
    </nav>
  </div>
</template>

<script>
import axios from 'axios';
import GroupButton from './GroupButton.vue';
import ScoreBoardButton from './ScoreBoardButton.vue';

export default {
  name: 'GroupNavbar',
  components: {
    GroupButton,
    ScoreBoardButton,
  },
  data() {
    return {
      groups_names: [],
    };
  },
  methods: {
    getGroupList() {
      const path = 'http://localhost:5000/groups/names';

      axios.get(path)
        .then((res) => {
          this.groups_names = res.data;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
  },
  created() {
    this.getGroupList();
  },
};
</script>
